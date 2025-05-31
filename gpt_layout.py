import openai
import json
import base64
from typing import Dict, Any

class GPTLayoutGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def generate_layout(self, prompt: str, image_base64: str = None) -> Dict[str, Any]:
        """
        GPT-4oを使用してサムネイルレイアウトを生成
        
        Args:
            prompt: レイアウト生成のプロンプト
            image_base64: base64エンコードされた画像（任意）
            
        Returns:
            レイアウト情報を含む辞書
        """
        
        system_prompt = """
        あなたはYouTubeサムネイルのレイアウトデザイナーです。
        ユーザーの要求に基づいて、以下のJSON形式でレイアウトを生成してください。
        
        サムネイルサイズ: 1280x720px
        
        JSON形式:
        {
          "background": {
            "type": "solid" | "gradient",
            "color": "#RRGGBB",
            "gradientStart": "#RRGGBB",
            "gradientEnd": "#RRGGBB"
          },
          "elements": [
            {
              "type": "text",
              "content": "テキスト内容",
              "x": 位置X,
              "y": 位置Y,
              "fontSize": フォントサイズ,
              "color": "#RRGGBB",
              "fontWeight": "normal" | "bold",
              "alignment": "left" | "center" | "right"
            },
            {
              "type": "image",
              "x": 位置X,
              "y": 位置Y,
              "width": 幅,
              "height": 高さ
            }
          ]
        }
        
        レスポンスはJSONのみで返してください。説明文は不要です。
        座標は0,0が左上基準です。
        文字サイズは読みやすさを重視してください。
        カラーコードは必ず#から始まる6桁の16進数で指定してください。
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 画像が提供されている場合は追加
        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像を使用してレイアウトを作成してください。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            })
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # JSONの抽出（コードブロックがある場合の対応）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            layout_data = json.loads(response_text)
            
            # レイアウトデータの検証・補正
            layout_data = self._validate_and_fix_layout(layout_data)
            
            return layout_data
            
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            return self._get_fallback_layout()
        except Exception as e:
            print(f"GPT API呼び出しエラー: {e}")
            return self._get_fallback_layout()
    
    def _validate_and_fix_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レイアウトデータの検証と修正
        """
        # デフォルト背景の設定
        if "background" not in layout_data:
            layout_data["background"] = {
                "type": "solid",
                "color": "#FFFFFF"
            }
        
        # 要素の検証
        if "elements" not in layout_data:
            layout_data["elements"] = []
        
        for element in layout_data["elements"]:
            # 座標の境界チェック
            if "x" in element:
                element["x"] = max(0, min(element["x"], 1280))
            if "y" in element:
                element["y"] = max(0, min(element["y"], 720))
            
            # テキスト要素の検証
            if element.get("type") == "text":
                if "fontSize" not in element:
                    element["fontSize"] = 48
                if "color" not in element:
                    element["color"] = "#000000"
                if "fontWeight" not in element:
                    element["fontWeight"] = "bold"
                if "alignment" not in element:
                    element["alignment"] = "left"
            
            # 画像要素の検証
            if element.get("type") == "image":
                if "width" not in element:
                    element["width"] = 300
                if "height" not in element:
                    element["height"] = 300
        
        return layout_data
    
    def _get_fallback_layout(self) -> Dict[str, Any]:
        """
        エラー時のフォールバックレイアウト
        """
        return {
            "background": {
                "type": "gradient",
                "gradientStart": "#FF6B6B",
                "gradientEnd": "#4ECDC4"
            },
            "elements": [
                {
                    "type": "text",
                    "content": "YouTubeサムネイル",
                    "x": 100,
                    "y": 100,
                    "fontSize": 72,
                    "color": "#FFFFFF",
                    "fontWeight": "bold",
                    "alignment": "left"
                },
                {
                    "type": "image",
                    "x": 800,
                    "y": 200,
                    "width": 400,
                    "height": 400
                }
            ]
        }