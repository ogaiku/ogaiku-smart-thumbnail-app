import requests
import io
from PIL import Image
from typing import Optional

class BackgroundRemover:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.remove.bg/v1.0/removebg"
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove.bg APIを使用して背景を除去
        
        Args:
            image: PIL画像オブジェクト
            
        Returns:
            背景が除去された透過PNG画像
        """
        try:
            # PIL画像をバイト形式に変換
            img_buffer = io.BytesIO()
            
            # 元の画像形式を保持
            original_format = image.format if image.format else 'PNG'
            image.save(img_buffer, format=original_format)
            img_buffer.seek(0)
            
            # Remove.bg APIにリクエスト送信
            response = requests.post(
                self.api_url,
                files={'image_file': img_buffer.getvalue()},
                data={'size': 'auto'},
                headers={'X-Api-Key': self.api_key}
            )
            
            if response.status_code == 200:
                # 成功時は透過PNG画像を返す
                result_image = Image.open(io.BytesIO(response.content))
                return result_image
            else:
                print(f"Remove.bg API エラー: {response.status_code}")
                print(f"エラー詳細: {response.text}")
                # エラー時は元画像を返す
                return self._create_fallback_image(image)
                
        except requests.exceptions.RequestException as e:
            print(f"ネットワークエラー: {e}")
            return self._create_fallback_image(image)
        except Exception as e:
            print(f"背景除去処理エラー: {e}")
            return self._create_fallback_image(image)
    
    def _create_fallback_image(self, original_image: Image.Image) -> Image.Image:
        """
        APIエラー時のフォールバック処理
        元画像をRGBAモードに変換して透過対応画像として返す
        """
        try:
            # RGBAモードに変換（透過対応）
            if original_image.mode != 'RGBA':
                rgba_image = original_image.convert('RGBA')
            else:
                rgba_image = original_image.copy()
            
            # 簡易的な背景除去処理（白背景の場合）
            rgba_image = self._simple_background_removal(rgba_image)
            
            return rgba_image
        except Exception as e:
            print(f"フォールバック処理エラー: {e}")
            # 最終手段として元画像をRGBAに変換して返す
            return original_image.convert('RGBA')
    
    def _simple_background_removal(self, image: Image.Image) -> Image.Image:
        """
        簡易的な背景除去処理
        白い背景を透明にする
        """
        try:
            data = image.getdata()
            new_data = []
            
            for item in data:
                # 白に近い色を透明にする（閾値：240）
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))  # 透明
                else:
                    new_data.append(item)
            
            image.putdata(new_data)
            return image
        except Exception as e:
            print(f"簡易背景除去エラー: {e}")
            return image
    
    def test_api_connection(self) -> bool:
        """
        Remove.bg APIの接続テスト
        
        Returns:
            接続成功時True、失敗時False
        """
        try:
            # 小さなテスト画像を作成
            test_image = Image.new('RGB', (100, 100), color='white')
            img_buffer = io.BytesIO()
            test_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            response = requests.post(
                self.api_url,
                files={'image_file': img_buffer.getvalue()},
                data={'size': 'preview'},
                headers={'X-Api-Key': self.api_key},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"API接続テストエラー: {e}")
            return False