import argparse
from datetime import timedelta
import logging
import os
from typing import Optional
import alibabacloud_oss_v2 as oss, models


class AliyunOSS:
    def __init__(self, endpoint, region, access_key_id, access_key_secret, bucket_name):
        self._endpoint = endpoint
        self._credentials = oss.credentials.StaticCredentialsProvider(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        self._bucket_name = bucket_name
        # 加载SDK的默认配置，并设置凭证提供者
        self._cfg = oss.config.load_default()
        self._cfg.credentials_provider = self._credentials

        # 设置配置中的区域信息
        self._cfg.region = region

        # 如果提供了endpoint参数，则设置配置中的endpoint
        if self._endpoint is not None:
            self._cfg.endpoint = self._endpoint

        # 使用配置好的信息创建OSS客户端
        self.client = oss.Client(self._cfg)


    def upload_file(self, file_path, object_name=None) -> Optional[models.PutObjectResult]:
        # 执行上传对象的请求，直接从文件上传
        # 指定存储空间名称、对象名称和本地文件路径
        result = self.client.put_object_from_file(
            oss.PutObjectRequest(
                bucket=self._bucket_name,
                key=object_name if object_name else os.path.basename(file_path)
            ),
            file_path
        )
        return result
    

    def get_presign_url(self, object_name, expires=600) -> Optional[str]:
        # 生成预签名的GET请求
        pre_result = self.client.presign(
            oss.GetObjectRequest(
                bucket=self._bucket_name,  # 指定存储空间名称
                key=object_name,        # 指定对象键名
            ),
            expires=timedelta(seconds=expires),
        )
        # 打印预签名请求的方法、过期时间和URL
        logging.info(f'method: {pre_result.method},'
            f' expiration: {pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z")},'
            f' url: {pre_result.url}'
        )
        return pre_result.url
    

    def download_file(self, object_name, file_path=None) -> Optional[str]:
        if file_path is None:
            if not os.path.exists("./temp"):
                os.makedirs("./temp")
            file_path = os.path.join("./temp", object_name)
        self.client.get_object_to_file(
            bucket_name=self._bucket_name,
            object_name=object_name,
            file_path=file_path,
        )
        return file_path


if __name__ == "__main__":
    ali_oss = AliyunOSS(
        endpoint="oss-cn-guangzhou.aliyuncs.com",
        region="cn-guangzhou",
        access_key_id=os.environ.get("ALI_OSS_AK_ID"),
        access_key_secret=os.environ.get("ALI_OSS_AK_SK"),
        bucket_name="yorc",
    )


    # result = ali_oss.upload_file("./BV1ZgmYBrEWo.mp3")

    # # 输出请求的结果信息，包括状态码、请求ID、内容MD5、ETag、CRC64校验码、版本ID和服务器响应时间
    # print(f'status code: {result.status_code},'
    #     f' request id: {result.request_id},'
    #     f' content md5: {result.content_md5},'
    #     f' etag: {result.etag},'
    #     f' hash crc64: {result.hash_crc64},'
    #     f' version id: {result.version_id},'
    #     f' server time: {result.headers.get("x-oss-server-time")},'
    # )
    
    ali_oss.get_presign_url("BV1ZgmYBrEWo.mp3", expires=300)