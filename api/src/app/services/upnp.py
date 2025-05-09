import asyncio
import socket
import netifaces
import time
import os
import aiohttp
from async_upnp_client.client import UpnpDevice
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.aiohttp import AiohttpSessionRequester
from async_upnp_client.search import async_search
from .logger import logger
from typing import Dict, Any

class UPNPService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UPNPService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.upnp = None
            self.error_message = None
            self.gateway_info = None  # 网关信息
            self.devices = []  # 所有发现的UPnP设备列表
            self.igd_device = None  # IGD设备（用于端口转发）
            self.session = None
            self.initialized = False
            self.interface_ip = None
            self._status_cache = None
            self._last_status_update = 0
            self._status_cache_ttl = 30  # 状态缓存有效期（秒）
            self._mappings_cache = None  # 端口映射缓存
            self._last_mappings_update = 0  # 端口映射最后更新时间
            self._mappings_cache_ttl = 30  # 端口映射缓存有效期（秒）
            self.upnp_factory = None
            self._initialized = True

    async def initialize(self):
        """异步初始化UPnP服务"""
        if self.initialized:
            return

        try:
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
            self.upnp_factory = UpnpFactory(self.session)
            
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
                        await async_search(
                            device_discovered,
                            timeout=10,  # 增加超时时间到10秒
                            source=(self.interface_ip, 0),  # 指定源IP和端口（0表示自动分配）
                            search_target="urn:schemas-upnp-org:device:InternetGatewayDevice:1"  # 只搜索IGD设备
                        )
                        logger.info(f"发现 {len(self.devices)} 个设备")
                        
                        if self.devices:
                            # 获取发现的设备信息
                            logger.info("正在获取设备信息...")
                            for device_info in self.devices:
                                logger.info(f"设备信息: {device_info}")
                            break
                        elif i < max_retries - 1:
                            logger.warning(f"未发现设备，等待后重试...")
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
                
                # 初始化端口映射缓存
                await self._update_mappings_cache()
                
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
            raise Exception("UPnP服务未初始化，请先调用initialize()")
        if self.upnp is None:
            raise Exception(f"UPnP服务未初始化: {self.error_message}")

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

    def validate_port(self, port: int) -> bool:
        """验证端口是否可用"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.close()
            return True
        except:
            return False

    def validate_port_mapping(self, external_port: int, protocol: str = 'TCP') -> bool:
        """验证端口映射是否已存在"""
        self._check_initialized()
        # TODO: 实现端口映射验证
        return False

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
                
    async def _update_mappings_cache(self):
        """更新端口映射缓存"""
        try:
            mappings = []
            
            # 获取网关设备
            if not self.gateway_info or not self.gateway_info.get('ip'):
                logger.error("未找到网关信息")
                return None
                
            gateway_ip = self.gateway_info['ip']
            logger.info(f"正在从网关 {gateway_ip} 获取端口映射...")
            
            # 遍历所有发现的设备
            for device_info in self.devices:
                device_url = device_info.get('LOCATION', '')
                if not device_url:
                    continue
                    
                # 检查是否是网关设备
                if gateway_ip not in device_url:
                    continue
                    
                try:
                    logger.info(f"正在创建设备对象: {device_url}")
                    # 创建设备对象
                    device = await self.upnp.async_create_device(device_url)
                    if not device:
                        logger.warning("创建设备对象失败")
                        continue
                        
                    # 打印设备信息
                    logger.info(f"设备类型: {device.device_type}")
                    logger.info(f"设备服务: {[s.service_type for s in device.services.values()]}")
                    
                    # 递归查找WANIPConnection服务
                    wan_ip_service = self.find_wan_ip_service(device)
                    if not wan_ip_service:
                        logger.warning("未找到WANIPConnection服务")
                        continue
                    
                    try:
                        # 获取连接状态
                        status_result = await wan_ip_service.async_call_action('GetStatusInfo')
                        logger.info(f"连接状态: {status_result}")
                        
                        # 获取外部IP地址
                        external_ip_result = await wan_ip_service.async_call_action('GetExternalIPAddress')
                        external_ip = external_ip_result.get('NewExternalIPAddress')
                        logger.info(f"外部IP地址: {external_ip}")
                        
                        # 获取端口映射列表
                        index = 0
                        while True:
                            try:
                                logger.info(f"正在获取第 {index} 个端口映射")
                                result = await wan_ip_service.async_call_action(
                                    'GetGenericPortMappingEntry',
                                    NewPortMappingIndex=index
                                )
                                
                                # 解析端口映射信息
                                mapping = {
                                    "external_port": result.get('NewExternalPort'),
                                    "internal_port": result.get('NewInternalPort'),
                                    "protocol": result.get('NewProtocol'),
                                    "internal_ip": result.get('NewInternalClient'),
                                    "enabled": result.get('NewEnabled', True),
                                    "description": result.get('NewPortMappingDescription', ''),
                                    "lease_duration": result.get('NewLeaseDuration', 0)
                                }
                                logger.info(f"找到端口映射: {mapping}")
                                mappings.append(mapping)
                                index += 1
                            except Exception as e:
                                logger.info(f"获取端口映射失败: {str(e)}")
                                # 没有更多端口映射时退出
                                if index == 0:
                                    logger.info("没有找到任何端口映射")
                                else:
                                    logger.info(f"已获取所有端口映射，共 {index} 条")
                                break
                    except Exception as e:
                        logger.warning(f"获取端口映射失败: {str(e)}")
                        continue
                    
                except Exception as e:
                    logger.warning(f"处理网关设备失败: {str(e)}")
                    continue

            # 更新缓存
            self._mappings_cache = {
                "status": "success",
                "mappings": mappings,
                "connection_info": {
                    "status": status_result.get('NewConnectionStatus'),
                    "uptime": status_result.get('NewUptime'),
                    "last_error": status_result.get('NewLastConnectionError'),
                    "external_ip": external_ip
                }
            }
            self._last_mappings_update = time.time()
            logger.info(f"更新端口映射缓存成功，共 {len(mappings)} 条记录")
        except Exception as e:
            logger.error(f"更新端口映射缓存失败: {str(e)}")
            self._mappings_cache = None

    def get_port_mappings(self):
        """获取所有端口映射"""
        self._check_initialized()

        # 检查缓存是否有效
        current_time = time.time()
        if (self._mappings_cache is not None and 
            current_time - self._last_mappings_update < self._mappings_cache_ttl):
            return self._mappings_cache

        # 缓存无效，更新缓存
        # self._update_mappings_cache()
        return self._mappings_cache

    async def add_port_mapping(self, external_port: int, internal_port: int, protocol: str, local_ip: str, description: str = "", lease_duration: int = 0) -> Dict[str, Any]:
        """添加端口映射"""
        try:
            # 获取网关设备
            if not self.gateway_info or not self.gateway_info.get('ip'):
                logger.error("未找到网关信息")
                return {"status": "error", "message": "未找到网关信息"}
            
            gateway_ip = self.gateway_info['ip']
            logger.info(f"正在从网关 {gateway_ip} 添加端口映射...")
            
            # 遍历所有发现的设备
            for device_info in self.devices:
                device_url = device_info.get('LOCATION', '')
                if not device_url:
                    continue
                
                # 检查是否是网关设备
                if gateway_ip not in device_url:
                    continue
                
                try:
                    # 创建设备对象
                    device = await self.upnp.async_create_device(device_url)
                    if not device:
                        logger.warning("创建设备对象失败")
                        continue
                        
                    # 递归查找WANIPConnection服务
                    wan_ip_service = self.find_wan_ip_service(device)
                    if not wan_ip_service:
                        logger.warning("未找到WANIPConnection服务")
                        continue
                    
                    try:
                        logger.info(f"正在添加端口映射: {external_port} -> {local_ip}:{internal_port} ({protocol})")
                          
                        # 打印所有参数
                        params = {
                            'NewRemoteHost': "",
                            'NewExternalPort': external_port,
                            'NewProtocol': protocol.upper(),
                            'NewInternalPort': internal_port,
                            'NewInternalClient': local_ip,
                            'NewEnabled': True,
                            'NewPortMappingDescription': description,
                            'NewLeaseDuration': lease_duration
                        }
                        logger.info(f"准备调用AddPortMapping，参数: {params}")
                    
                        result = await wan_ip_service.async_call_action(
                            'AddPortMapping',
                            NewRemoteHost="",
                            NewExternalPort=int(external_port),
                            NewProtocol=protocol.upper(),
                            NewInternalPort=int(internal_port),
                            NewInternalClient=local_ip,
                            NewEnabled=True,
                            NewPortMappingDescription=description,
                            NewLeaseDuration=lease_duration
                        )
                        
                        logger.info(f"端口映射添加成功: {result}")
                        return {
                            "status": "success",
                            "message": "端口映射添加成功",
                            "result": result
                        }
                        
                    except Exception as e:
                        logger.warning(f"添加端口映射失败: {str(e)}")
                        return {
                            "status": "error",
                            "message": f"添加端口映射失败: {str(e)}"
                        }
                    
                except Exception as e:
                    logger.warning(f"处理网关设备失败: {str(e)}")
                    continue
                
            return {
                "status": "error",
                "message": "未找到可用的网关设备"
            }
            
        except Exception as e:
            logger.error(f"添加端口映射失败: {str(e)}")
            return {
                "status": "error",
                "message": f"添加端口映射失败: {str(e)}"
            }

    async def delete_port_mapping(self, external_port: int, protocol: str = 'TCP'):
        """删除端口映射"""
        self._check_initialized()

        try:
            # 获取网关设备
            if not self.gateway_info or not self.gateway_info.get('ip'):
                logger.error("未找到网关信息")
                return {"status": "error", "message": "未找到网关信息"}
            
            gateway_ip = self.gateway_info['ip']
            logger.info(f"正在从网关 {gateway_ip} 删除端口映射...")
            
            # 遍历所有发现的设备
            for device_info in self.devices:
                device_url = device_info.get('LOCATION', '')
                if not device_url:
                    continue
                
                # 检查是否是网关设备
                if gateway_ip not in device_url:
                    continue
                
                try:
                    # 创建设备对象
                    device = await self.upnp.async_create_device(device_url)
                    if not device:
                        logger.warning("创建设备对象失败")
                        continue
                        
                    # 递归查找WANIPConnection服务
                    wan_ip_service = self.find_wan_ip_service(device)
                    if not wan_ip_service:
                        logger.warning("未找到WANIPConnection服务")
                        continue
                    
                    try:
                        # 打印服务信息
                        logger.info(f"WANIPConnection服务信息: {wan_ip_service}")
                        logger.info(f"服务类型: {wan_ip_service.service_type}")
                        logger.info(f"服务ID: {wan_ip_service.service_id}")
                        
                        # 打印动作信息
                        delete_port_mapping_action = wan_ip_service.action('DeletePortMapping')
                        if delete_port_mapping_action:
                            logger.info(f"DeletePortMapping动作信息: {delete_port_mapping_action}")
                            logger.info(f"动作参数: {delete_port_mapping_action.arguments}")
                        
                        # 打印所有参数
                        params = {
                            'NewRemoteHost': "",
                            'NewExternalPort': int(external_port),  # 转换为字符串
                            'NewProtocol': protocol.upper()
                        }
                        logger.info(f"准备调用DeletePortMapping，参数: {params}")
                        
                        result = await wan_ip_service.async_call_action(
                            'DeletePortMapping',
                            **params
                        )
                        
                        logger.info(f"端口映射删除成功: {result}")
                        
                        # 清除缓存
                        self._mappings_cache = None
                        
                        return {
                            "status": "success",
                            "message": "端口映射删除成功",
                            "mapping": {
                                "external_port": external_port,
                                "protocol": protocol
                            }
                        }
                        
                    except Exception as e:
                        logger.warning(f"删除端口映射失败: {str(e)}")
                        # 打印更详细的错误信息
                        if hasattr(e, 'args'):
                            logger.warning(f"错误参数: {e.args}")
                        if hasattr(e, 'response'):
                            logger.warning(f"错误响应: {e.response}")
                        return {
                            "status": "error",
                            "message": f"删除端口映射失败: {str(e)}"
                        }
                        
                except Exception as e:
                    logger.warning(f"处理网关设备失败: {str(e)}")
                    continue
                
            return {
                "status": "error",
                "message": "未找到可用的网关设备"
            }
            
        except Exception as e:
            logger.error(f"删除端口映射失败: {str(e)}")
            return {
                "status": "error",
                "message": f"删除端口映射失败: {str(e)}"
            } 