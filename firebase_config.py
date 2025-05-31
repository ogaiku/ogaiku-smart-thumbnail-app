import os
import json
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

# Firebase SDKのインポート（オプション）
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase SDK がインストールされていません。pip install firebase-admin でインストールしてください。")

class FirebaseManager:
    def __init__(self, config_path: Optional[str] = None):
        self.db = None
        self.bucket = None
        self.initialized = False
        
        if FIREBASE_AVAILABLE and config_path and os.path.exists(config_path):
            self._initialize_firebase(config_path)
    
    def _initialize_firebase(self, config_path: str):
        """
        Firebase を初期化
        """
        try:
            # 既に初期化されている場合はスキップ
            if firebase_admin._apps:
                app = firebase_admin.get_app()
            else:
                cred = credentials.Certificate(config_path)
                app = firebase_admin.initialize_app(cred, {
                    'storageBucket': 'your-project-id.appspot.com'  # 実際のプロジェクトIDに変更
                })
            
            self.db = firestore.client()
            self.bucket = storage.bucket()
            self.initialized = True
            print("Firebase 初期化完了")
            
        except Exception as e:
            print(f"Firebase 初期化エラー: {e}")
            self.initialized = False
    
    def save_thumbnail_data(self, thumbnail_data: Dict[str, Any]) -> Optional[str]:
        """
        サムネイルデータをFirestoreに保存
        
        Args:
            thumbnail_data: 保存するサムネイルデータ
            
        Returns:
            保存成功時はドキュメントID、失敗時はNone
        """
        if not self.initialized or not self.db:
            return None
        
        try:
            # ドキュメントデータの準備
            doc_data = {
                'id': str(uuid.uuid4()),
                'created_at': datetime.now(),
                'layout_data': thumbnail_data.get('layout', {}),
                'title': thumbnail_data.get('title', ''),
                'subtitle': thumbnail_data.get('subtitle', ''),
                'design_style': thumbnail_data.get('design_style', ''),
                'color_theme': thumbnail_data.get('color_theme', ''),
                'status': 'active'
            }
            
            # Firestoreに保存
            doc_ref = self.db.collection('thumbnails').add(doc_data)
            document_id = doc_ref[1].id
            
            print(f"サムネイルデータ保存完了: {document_id}")
            return document_id
            
        except Exception as e:
            print(f"Firestore 保存エラー: {e}")
            return None
    
    def get_thumbnail_data(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Firestoreからサムネイルデータを取得
        
        Args:
            document_id: ドキュメントID
            
        Returns:
            取得したデータ、失敗時はNone
        """
        if not self.initialized or not self.db:
            return None
        
        try:
            doc_ref = self.db.collection('thumbnails').document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                print(f"ドキュメントが見つかりません: {document_id}")
                return None
                
        except Exception as e:
            print(f"Firestore 取得エラー: {e}")
            return None
    
    def upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        """
        画像をFirebase Storageにアップロード
        
        Args:
            image_data: 画像のバイナリデータ
            filename: ファイル名
            
        Returns:
            アップロード成功時は公開URL、失敗時はNone
        """
        if not self.initialized or not self.bucket:
            return None
        
        try:
            # ユニークなファイル名を生成
            unique_filename = f"thumbnails/{uuid.uuid4().hex}_{filename}"
            
            # Storage にアップロード
            blob = self.bucket.blob(unique_filename)
            blob.upload_from_string(image_data, content_type='image/png')
            
            # 公開URLを生成
            blob.make_public()
            public_url = blob.public_url
            
            print(f"画像アップロード完了: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Storage アップロードエラー: {e}")
            return None
    
    def list_user_thumbnails(self, limit: int = 10) -> list:
        """
        ユーザーのサムネイル一覧を取得
        
        Args:
            limit: 取得件数の上限
            
        Returns:
            サムネイルデータのリスト
        """
        if not self.initialized or not self.db:
            return []
        
        try:
            docs = self.db.collection('thumbnails')\
                     .where('status', '==', 'active')\
                     .order_by('created_at', direction=firestore.Query.DESCENDING)\
                     .limit(limit)\
                     .stream()
            
            thumbnails = []
            for doc in docs:
                data = doc.to_dict()
                data['document_id'] = doc.id
                thumbnails.append(data)
            
            return thumbnails
            
        except Exception as e:
            print(f"一覧取得エラー: {e}")
            return []
    
    def delete_thumbnail(self, document_id: str) -> bool:
        """
        サムネイルデータを削除（論理削除）
        
        Args:
            document_id: ドキュメントID
            
        Returns:
            削除成功時はTrue、失敗時はFalse
        """
        if not self.initialized or not self.db:
            return False
        
        try:
            doc_ref = self.db.collection('thumbnails').document(document_id)
            doc_ref.update({
                'status': 'deleted',
                'deleted_at': datetime.now()
            })
            
            print(f"サムネイル削除完了: {document_id}")
            return True
            
        except Exception as e:
            print(f"削除エラー: {e}")
            return False

class LocalStorageManager:
    """
    Firebaseが使用できない場合のローカルストレージ代替
    """
    def __init__(self, storage_dir: str = "local_storage"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(f"{storage_dir}/thumbnails", exist_ok=True)
        os.makedirs(f"{storage_dir}/images", exist_ok=True)
    
    def save_thumbnail_data(self, thumbnail_data: Dict[str, Any]) -> str:
        """
        サムネイルデータをローカルファイルに保存
        """
        try:
            document_id = str(uuid.uuid4())
            
            doc_data = {
                'id': document_id,
                'created_at': datetime.now().isoformat(),
                'layout_data': thumbnail_data.get('layout', {}),
                'title': thumbnail_data.get('title', ''),
                'subtitle': thumbnail_data.get('subtitle', ''),
                'design_style': thumbnail_data.get('design_style', ''),
                'color_theme': thumbnail_data.get('color_theme', ''),
                'status': 'active'
            }
            
            file_path = f"{self.storage_dir}/thumbnails/{document_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
            return document_id
            
        except Exception as e:
            print(f"ローカル保存エラー: {e}")
            return None
    
    def get_thumbnail_data(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        ローカルファイルからサムネイルデータを取得
        """
        try:
            file_path = f"{self.storage_dir}/thumbnails/{document_id}.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            print(f"ローカル取得エラー: {e}")
            return None
    
    def save_image(self, image_data: bytes, filename: str) -> str:
        """
        画像をローカルに保存
        """
        try:
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = f"{self.storage_dir}/images/{unique_filename}"
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            return file_path
            
        except Exception as e:
            print(f"画像保存エラー: {e}")
            return None