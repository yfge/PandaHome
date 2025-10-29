from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkalidns.request.v20150109.DescribeDomainsRequest import DescribeDomainsRequest
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DeleteDomainRecordRequest import DeleteDomainRecordRequest
from ..config import settings
from .logger import logger
import json

class AliyunDNSService:
    def __init__(self):
        self.client = AcsClient(
            settings.ALIYUN_ACCESS_KEY_ID,
            settings.ALIYUN_ACCESS_KEY_SECRET,
            settings.ALIYUN_REGION_ID,
        )

    def get_domains_list(self):
        """获取域名列表"""
        request = DescribeDomainsRequest()
        request.set_accept_format('json')
        
        try:
            response = self.client.do_action_with_exception(request)
            response_data = json.loads(response)
            
            # 打印原始响应以便调试
            logger.info(f"原始域名列表响应: {response_data}")
            
            # 只返回域名、ID和状态信息
            simplified_domains = [
                {
                    "domain": domain["DomainName"],
                    "id": domain["DomainId"],
                    "status": domain.get("VersionName", "unknown")  # 使用 VersionName 作为状态
                }
                for domain in response_data.get("Domains", {}).get("Domain", [])
            ]
            
            return simplified_domains
        except (ClientException, ServerException) as e:
            raise Exception(f"获取域名列表失败: {str(e)}")
        except Exception as e:
            logger.error(f"处理域名列表时发生错误: {str(e)}")
            raise Exception(f"处理域名列表时发生错误: {str(e)}")

    def get_domain_records(self, domain_name: str):
        """获取域名解析记录"""
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)
        
        try:
            response = self.client.do_action_with_exception(request)
            return json.loads(response)
        except (ClientException, ServerException) as e:
            raise Exception(f"获取域名解析记录失败: {str(e)}")

    def validate_domain(self, domain_name: str) -> bool:
        """验证域名是否存在"""
        domains = self.get_domains_list()
        return any(domain['domain'] == domain_name for domain in domains)

    def validate_record(self, domain_name: str, rr: str) -> bool:
        """验证解析记录是否已存在"""
        records = self.get_domain_records(domain_name)
        return any(record['rr'] == rr for record in records)

    def add_domain_record(self, domain_name: str, rr: str, value: str):
        """添加域名解析记录"""
        request = AddDomainRecordRequest()
        request.set_accept_format('json')
        request.set_DomainName(domain_name)
        request.set_RR(rr)
        request.set_Type('A')
        request.set_Value(value)
        
        try:
            response = self.client.do_action_with_exception(request)
            return json.loads(response)
        except (ClientException, ServerException) as e:
            raise Exception(f"添加域名解析记录失败: {str(e)}")

    def delete_domain_record(self, record_id: str):
        """删除域名解析记录"""
        request = DeleteDomainRecordRequest()
        request.set_accept_format('json')
        request.set_RecordId(record_id)
        
        try:
            self.client.do_action_with_exception(request)
            logger.info(f"删除域名解析记录成功: {record_id}")
        except Exception as e:
            logger.error(f"删除域名解析记录失败: {str(e)}")
            raise Exception(f"删除域名解析记录失败: {str(e)}") 
