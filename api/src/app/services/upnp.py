from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
import time
from enum import Enum
from typing import Any

import aiohttp
import netifaces
from async_upnp_client.aiohttp import AiohttpSessionRequester
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.search import async_search

from .logger import logger


class UPNPErrorCode(str, Enum):
    UNAVAILABLE = "unavailable"
    INVALID_PORT = "invalid_port"
    INVALID_PROTOCOL = "invalid_protocol"
    INVALID_IP = "invalid_ip"
    INVALID_LEASE_DURATION = "invalid_lease_duration"
    MAPPING_EXISTS = "mapping_exists"
    MAPPING_NOT_FOUND = "mapping_not_found"
    GATEWAY_NOT_FOUND = "gateway_not_found"
    ACTION_FAILED = "action_failed"


class UPNPServiceError(RuntimeError):
    def __init__(self, code: UPNPErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class UPNPService:
    def __init__(
        self,
        *,
        status_cache_ttl_seconds: int = 30,
        mappings_cache_ttl_seconds: int = 30,
    ):
        self.upnp: UpnpFactory | None = None
        self.error_message: str | None = None
        self.gateway_info: dict[str, Any] | None = None  # 网关信息
        self.devices: list[dict[str, Any]] = []  # 所有发现的UPnP设备列表
        self.session: aiohttp.ClientSession | None = None
        self.initialized: bool = False
        self.interface_ip: str | None = None

        self._status_cache: dict[str, Any] | None = None
        self._last_status_update: float = 0
        self._status_cache_ttl = status_cache_ttl_seconds

        self._mappings_cache: dict[str, Any] | None = None  # 端口映射缓存
        self._last_mappings_update: float = 0  # 端口映射最后更新时间
        self._mappings_cache_ttl = mappings_cache_ttl_seconds  # 端口映射缓存有效期（秒）
        self._mappings_lock = asyncio.Lock()

    async def startup(self) -> None:
        await self.initialize()

    async def shutdown(self) -> None:
        await self.close()

    async def initialize(self):
        """异步初始化UPnP服务"""
        if self.initialized:
            return

        try:
            self.error_message = None
            self.devices = []
            self.gateway_info = None
            self.interface_ip = None
            # 获取默认网关
            logger.info("正在获取默认网关...")
            gateways = netifaces.gateways()
            default_gateway = None
            default_interface = None

            # 尝试从不同位置获取默认网关
            if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                default_gateway = gateways['default'][netifaces.AF_INET][0]
                default_interface = gateways['default'][netifaces.AF_INET][1]
            elif netifaces.AF_INET in gateways:
                # macOS上gateways[netifaces.AF_INET]是一个列表
                for gateway_info in gateways[netifaces.AF_INET]:
                    if gateway_info[0] is not None:
                        default_gateway = gateway_info[0]
                        default_interface = gateway_info[1]
                        break

            if default_gateway is None:
                logger.error("无法获取默认网关")
                raise Exception("无法获取默认网关")

            logger.info(f"默认网关: {default_gateway}")
            logger.info(f"默认接口: {default_interface}")

            # 记录网络接口信息
            logger.info("正在检查网络接口...")
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        logger.info(f"接口 {iface}: IP={addr.get('addr')}")

            # 设置网络接口
            if default_interface:
                # 获取接口的IP地址
                interface_addrs = netifaces.ifaddresses(default_interface)
                if netifaces.AF_INET in interface_addrs:
                    self.interface_ip = interface_addrs[netifaces.AF_INET][0]['addr']
                    logger.info(f"使用接口 {default_interface} (IP: {self.interface_ip})")
                    # 设置环境变量来指定网络接口
                    os.environ['UPNP_INTERFACE'] = self.interface_ip
                else:
                    logger.warning(f"接口 {default_interface} 没有IPv4地址，使用默认设置")
            else:
                logger.warning("未找到默认接口，使用默认设置")

            # 初始化UPnP
            logger.info("正在初始化UPnP...")
            # 创建aiohttp会话
            self.session = aiohttp.ClientSession()
            # 创建requester
            requester = AiohttpSessionRequester(self.session)
            self.upnp = UpnpFactory(requester)

            # 保存网关信息
            self.gateway_info = {
                "ip": default_gateway,
                "interface": default_interface,
                "local_ip": self.interface_ip
            }

            # 尝试发现设备
            logger.info(f"正在发现UPnP设备（网关: {default_gateway}）...")
            try:
                # 尝试多次发现设备
                max_retries = 5  # 增加重试次数

                async def device_discovered(device_info):
                    """设备发现回调函数"""
                    logger.info(f"发现设备: {device_info}")
                    # 检查设备是否已存在
                    for existing_device in self.devices:
                        if existing_device.get('LOCATION') == device_info.get('LOCATION'):
                            return
                    # 添加到设备列表
                    self.devices.append(device_info)

                for i in range(max_retries):
                    try:
                        logger.info(f"尝试发现设备 ({i+1}/{max_retries})...")
                        # 使用异步搜索，增加超时时间，指定网络接口
                        search_kwargs: dict[str, Any] = {
                            "timeout": 10,  # 增加超时时间到10秒
                            "search_target": "urn:schemas-upnp-org:device:InternetGatewayDevice:1",  # 只搜索IGD设备
                        }
                        if self.interface_ip:
                            search_kwargs["source"] = (self.interface_ip, 0)  # 指定源IP和端口（0表示自动分配）

                        await async_search(device_discovered, **search_kwargs)
                        logger.info(f"发现 {len(self.devices)} 个设备")

                        if self.devices:
                            # 获取发现的设备信息
                            logger.info("正在获取设备信息...")
                            for device_info in self.devices:
                                logger.info(f"设备信息: {device_info}")
                            break
                        elif i < max_retries - 1:
                            logger.warning("未发现设备，等待后重试...")
                            await asyncio.sleep(5)  # 增加等待时间到5秒
                            continue
                    except Exception as e:
                        if i < max_retries - 1:
                            logger.warning(f"设备发现失败，正在重试 ({i+1}/{max_retries}): {str(e)}")
                            await asyncio.sleep(5)  # 增加等待时间到5秒
                            continue
                        else:
                            raise

                # 检查设备发现结果
                if not self.devices:
                    logger.error("未发现UPnP设备，请检查：")
                    logger.error("1. 路由器是否支持UPnP")
                    logger.error("2. 路由器UPnP功能是否已启用")
                    logger.error("3. 防火墙是否允许UPnP通信（UDP 1900端口）")
                    logger.error(f"4. 当前网关 {default_gateway} 是否支持UPnP")
                    raise Exception("未发现UPnP设备")

                logger.info("UPnP服务初始化成功")
                self.initialized = True

                # 更新状态缓存
                self._update_status_cache()

                # 初始化端口映射缓存（失败也不影响整体服务启动）
                try:
                    await self._update_mappings_cache()
                except Exception as exc:
                    logger.warning(f"初始化端口映射缓存失败: {exc}")

            except Exception as e:
                logger.error(f"UPnP服务初始化失败: {str(e)}")
                raise Exception(f"UPnP服务初始化失败: {str(e)}")
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"UPnP服务初始化失败: {self.error_message}")
            self.upnp = None
            # 关闭aiohttp会话
            if self.session:
                await self.session.close()
                self.session = None
            # 更新状态缓存为错误状态
            self._update_status_cache()

    def _update_status_cache(self):
        """更新状态缓存"""
        if not self.initialized or self.upnp is None:
            self._status_cache = {
                "status": "unavailable",
                "error": self.error_message or "UPnP服务未初始化"
            }
        else:
            try:
                # 将设备信息转换为可序列化的字典
                devices_list = []
                for device in self.devices:
                    device_dict = {}
                    for key, value in device.items():
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            device_dict[key] = value
                        else:
                            device_dict[key] = str(value)
                    devices_list.append(device_dict)

                self._status_cache = {
                    "status": "available",
                    "gateway": self.gateway_info,
                    "devices": devices_list
                }
            except Exception as e:
                self.error_message = str(e)
                self._status_cache = {
                    "status": "unavailable",
                    "error": self.error_message
                }
        self._last_status_update = time.time()

    async def close(self):
        """关闭UPnP服务"""
        if self.session:
            await self.session.close()
            self.session = None
        self.initialized = False
        self._status_cache = None
        self._mappings_cache = None

    def get_status(self):
        """获取UPnP服务状态（带缓存）"""
        current_time = time.time()

        # 检查缓存是否有效
        if (self._status_cache is not None and
            current_time - self._last_status_update < self._status_cache_ttl):
            return self._status_cache

        self._update_status_cache()
        return self._status_cache

    def _check_initialized(self):
        """检查UPnP服务是否已初始化"""
        if not self.initialized:
            raise UPNPServiceError(
                UPNPErrorCode.UNAVAILABLE,
                self.error_message or "UPnP服务未初始化，请先调用initialize()",
            )
        if self.upnp is None:
            raise UPNPServiceError(
                UPNPErrorCode.UNAVAILABLE,
                f"UPnP服务不可用: {self.error_message}",
            )

    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 获取默认网关的IP地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.error(f"获取本机IP地址失败: {str(e)}")
            raise Exception(f"获取本机IP地址失败: {str(e)}")

    def _normalize_protocol(self, protocol: str) -> str:
        value = str(protocol).upper()
        if value not in {"TCP", "UDP"}:
            raise UPNPServiceError(UPNPErrorCode.INVALID_PROTOCOL, f"不支持的协议类型: {protocol}")
        return value

    def _validate_port_number(self, port: int, field_name: str) -> None:
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise UPNPServiceError(UPNPErrorCode.INVALID_PORT, f"{field_name} 必须在 1-65535 之间")

    def _validate_local_ip(self, local_ip: str) -> None:
        if not local_ip:
            return
        try:
            ipaddress.ip_address(local_ip)
        except ValueError as exc:
            raise UPNPServiceError(UPNPErrorCode.INVALID_IP, f"无效的 IP 地址: {local_ip}") from exc

    def _validate_lease_duration(self, lease_duration: int) -> None:
        if lease_duration < 0:
            raise UPNPServiceError(UPNPErrorCode.INVALID_LEASE_DURATION, "lease_duration 不能为负数")

    def find_wan_ip_service(self, device):
        """递归查找WANIPConnection服务"""
        if not device:
            return None

        # 检查当前设备的服务
        for service in device.services.values():
            if service.service_type == "urn:schemas-upnp-org:service:WANIPConnection:1":
                return service

        # 检查嵌入式设备
        if hasattr(device, 'embedded_devices'):
            for embedded_device in device.embedded_devices.values():
                logger.info(f"检查嵌入式设备: {embedded_device.device_type}")
                logger.info(f"嵌入式设备服务: {[s.service_type for s in embedded_device.services.values()]}")

                # 递归检查嵌入式设备
                service = self.find_wan_ip_service(embedded_device)
                if service:
                    return service

        return None

    async def _get_gateway_wan_service(self):
        self._check_initialized()
        if not self.gateway_info or not self.gateway_info.get("ip"):
            raise UPNPServiceError(UPNPErrorCode.GATEWAY_NOT_FOUND, "未找到网关信息")

        gateway_ip = self.gateway_info["ip"]
        logger.info(f"正在从网关 {gateway_ip} 获取WANIPConnection服务...")

        for device_info in self.devices:
            device_url = device_info.get("LOCATION", "")
            if not device_url:
                continue
            if gateway_ip not in device_url:
                continue

            logger.info(f"正在创建设备对象: {device_url}")
            device = await self.upnp.async_create_device(device_url)
            if not device:
                logger.warning("创建设备对象失败")
                continue

            wan_ip_service = self.find_wan_ip_service(device)
            if not wan_ip_service:
                logger.warning("未找到WANIPConnection服务")
                continue

            return wan_ip_service

        raise UPNPServiceError(UPNPErrorCode.UNAVAILABLE, "未找到可用的网关设备")

    async def _update_mappings_cache(self) -> None:
        """更新端口映射缓存"""
        async with self._mappings_lock:
            mappings: list[dict[str, Any]] = []
            connection_info: dict[str, Any] = {
                "status": None,
                "uptime": None,
                "last_error": None,
                "external_ip": None,
            }

            wan_ip_service = await self._get_gateway_wan_service()

            # 获取连接状态 / 外部 IP（非关键数据，尽量 best-effort）
            try:
                status_result = await wan_ip_service.async_call_action("GetStatusInfo")
                connection_info["status"] = status_result.get("NewConnectionStatus")
                connection_info["uptime"] = status_result.get("NewUptime")
                connection_info["last_error"] = status_result.get("NewLastConnectionError")
            except Exception as exc:
                logger.warning(f"获取连接状态失败: {exc}")

            try:
                external_ip_result = await wan_ip_service.async_call_action("GetExternalIPAddress")
                connection_info["external_ip"] = external_ip_result.get("NewExternalIPAddress")
            except Exception as exc:
                logger.warning(f"获取外部IP地址失败: {exc}")

            # 获取端口映射列表
            index = 0
            while True:
                try:
                    result = await wan_ip_service.async_call_action(
                        "GetGenericPortMappingEntry",
                        NewPortMappingIndex=index,
                    )

                    mapping = {
                        "external_port": result.get("NewExternalPort"),
                        "internal_port": result.get("NewInternalPort"),
                        "protocol": result.get("NewProtocol"),
                        "internal_ip": result.get("NewInternalClient"),
                        "enabled": result.get("NewEnabled", True),
                        "description": result.get("NewPortMappingDescription", ""),
                        "lease_duration": result.get("NewLeaseDuration", 0),
                    }
                    mappings.append(mapping)
                    index += 1
                except Exception as exc:
                    logger.info(f"获取端口映射结束: {exc}")
                    break

            self._mappings_cache = {
                "status": "success",
                "mappings": mappings,
                "connection_info": connection_info,
            }
            self._last_mappings_update = time.time()
            logger.info(f"更新端口映射缓存成功，共 {len(mappings)} 条记录")

    async def get_port_mappings(self) -> dict[str, Any]:
        """获取所有端口映射（带缓存，必要时刷新）"""
        self._check_initialized()

        current_time = time.time()
        if (
            self._mappings_cache is not None
            and current_time - self._last_mappings_update < self._mappings_cache_ttl
        ):
            return self._mappings_cache

        await self._update_mappings_cache()
        if self._mappings_cache is None:
            raise UPNPServiceError(UPNPErrorCode.ACTION_FAILED, "获取端口映射失败")
        return self._mappings_cache

    async def add_port_mapping(
        self,
        external_port: int,
        internal_port: int,
        protocol: str,
        local_ip: str,
        description: str = "",
        lease_duration: int = 0,
    ) -> dict[str, Any]:
        """添加端口映射"""
        self._check_initialized()
        normalized_protocol = self._normalize_protocol(protocol)
        self._validate_port_number(external_port, "external_port")
        self._validate_port_number(internal_port, "internal_port")
        self._validate_lease_duration(lease_duration)
        if local_ip:
            self._validate_local_ip(local_ip)

        resolved_local_ip = local_ip or self.interface_ip or self.get_local_ip()
        cache = await self.get_port_mappings()
        for mapping in cache.get("mappings", []):
            try:
                existing_port = int(mapping.get("external_port"))
            except Exception:
                continue
            existing_protocol = str(mapping.get("protocol", "")).upper()
            if existing_port == external_port and existing_protocol == normalized_protocol:
                raise UPNPServiceError(UPNPErrorCode.MAPPING_EXISTS, "映射已存在")

        try:
            wan_ip_service = await self._get_gateway_wan_service()

            logger.info(
                f"正在添加端口映射: {external_port} -> {resolved_local_ip}:{internal_port} ({normalized_protocol})"
            )

            result = await wan_ip_service.async_call_action(
                "AddPortMapping",
                NewRemoteHost="",
                NewExternalPort=int(external_port),
                NewProtocol=normalized_protocol,
                NewInternalPort=int(internal_port),
                NewInternalClient=resolved_local_ip,
                NewEnabled=True,
                NewPortMappingDescription=description,
                NewLeaseDuration=int(lease_duration),
            )

            # 刷新缓存（失败不影响本次成功返回）
            self._mappings_cache = None
            self._last_mappings_update = 0
            try:
                await self._update_mappings_cache()
            except Exception as exc:
                logger.warning(f"刷新端口映射缓存失败: {exc}")

            return {"status": "success", "message": "端口映射添加成功", "result": result}
        except UPNPServiceError:
            raise
        except Exception as exc:
            logger.error(f"添加端口映射失败: {exc}")
            raise UPNPServiceError(UPNPErrorCode.ACTION_FAILED, f"添加端口映射失败: {exc}") from exc

    async def delete_port_mapping(self, external_port: int, protocol: str = 'TCP'):
        """删除端口映射"""
        self._check_initialized()
        normalized_protocol = self._normalize_protocol(protocol)
        self._validate_port_number(external_port, "external_port")

        cache = await self.get_port_mappings()
        found = False
        for mapping in cache.get("mappings", []):
            try:
                existing_port = int(mapping.get("external_port"))
            except Exception:
                continue
            existing_protocol = str(mapping.get("protocol", "")).upper()
            if existing_port == external_port and existing_protocol == normalized_protocol:
                found = True
                break
        if not found:
            raise UPNPServiceError(UPNPErrorCode.MAPPING_NOT_FOUND, "端口映射不存在")

        try:
            wan_ip_service = await self._get_gateway_wan_service()

            params = {
                "NewRemoteHost": "",
                "NewExternalPort": int(external_port),
                "NewProtocol": normalized_protocol,
            }
            result = await wan_ip_service.async_call_action("DeletePortMapping", **params)

            self._mappings_cache = None
            self._last_mappings_update = 0
            try:
                await self._update_mappings_cache()
            except Exception as exc:
                logger.warning(f"刷新端口映射缓存失败: {exc}")

            return {
                "status": "success",
                "message": "端口映射删除成功",
                "result": result,
                "mapping": {
                    "external_port": external_port,
                    "protocol": normalized_protocol,
                },
            }
        except UPNPServiceError:
            raise
        except Exception as exc:
            logger.error(f"删除端口映射失败: {exc}")
            raise UPNPServiceError(UPNPErrorCode.ACTION_FAILED, f"删除端口映射失败: {exc}") from exc
