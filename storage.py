"""文件存储抽象层 - 支持本地存储与腾讯云 COS"""

import os
import uuid
import shutil
from datetime import datetime
from config import Config


class LocalStorage:
    """本地文件存储"""

    def __init__(self, base_path):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_path(self, key):
        return os.path.join(self.base_path, key.lstrip('/'))

    def save(self, file_obj, filename):
        """保存文件，返回 storage key"""
        ext = os.path.splitext(filename)[1].lower()
        key = f"{datetime.utcnow().strftime('%Y/%m')}/{uuid.uuid4().hex}{ext}"
        full_path = self._get_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file_obj.seek(0)
        file_obj.save(full_path)
        return key

    def delete(self, key):
        """删除文件"""
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

    def url(self, key):
        """返回文件访问 URL（本地存储返回静态路径）"""
        return f'/uploads/{key.lstrip("/")}'

    def exists(self, key):
        return os.path.exists(self._get_path(key))


class COSStorage:
    """腾讯云 COS 存储"""

    def __init__(self, secret_id, secret_key, region, bucket):
        self.enabled = bool(secret_id and secret_key and bucket)
        self._client = None
        if self.enabled:
            try:
                from qcloud_cos import CosConfig, CosS3Client
                config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
                self._client = CosS3Client(config)
                self._bucket = bucket
            except ImportError:
                self.enabled = False
            except Exception:
                self.enabled = False

    def save(self, file_obj, filename):
        ext = os.path.splitext(filename)[1].lower()
        key = f"materials/{datetime.utcnow().strftime('%Y/%m')}/{uuid.uuid4().hex}{ext}"
        if self._client:
            try:
                file_obj.seek(0)
                self._client.put_object(
                    Bucket=self._bucket,
                    Body=file_obj.read(),
                    Key=key,
                )
            except Exception:
                pass
        return key

    def delete(self, key):
        if self._client:
            try:
                self._client.delete_object(Bucket=self._bucket, Key=key)
            except Exception:
                pass

    def url(self, key):
        return f'https://{self._bucket}.cos.{Config.COS_REGION}.myqcloud.com/{key}'

    def exists(self, key):
        if self._client:
            try:
                self._client.head_object(Bucket=self._bucket, Key=key)
                return True
            except Exception:
                return False
        return False


# 初始化存储引擎
_local = LocalStorage(Config.UPLOAD_FOLDER)
_cos = COSStorage(Config.COS_SECRET_ID, Config.COS_SECRET_KEY,
                  Config.COS_REGION, Config.COS_BUCKET)


def get_storage():
    """获取当前活跃的存储引擎（COS 优先，不可用时降级到本地）"""
    return _cos if _cos.enabled else _local


def save_file(file_obj, filename):
    """保存文件"""
    return get_storage().save(file_obj, filename)


def delete_file(key):
    """删除文件"""
    get_storage().delete(key)


def file_url(key):
    """获取文件 URL"""
    return get_storage().url(key)


def file_exists(key):
    """检查文件是否存在"""
    return get_storage().exists(key)


# 提供给 Flask 的本地文件服务
def serve_uploaded_file(key):
    """Flask 路由中使用的本地文件发送函数"""
    import flask
    path = _local._get_path(key)
    if os.path.exists(path):
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        return flask.send_from_directory(directory, filename)
    flask.abort(404)
