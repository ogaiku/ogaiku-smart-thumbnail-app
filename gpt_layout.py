import openai
import json
import base64
from typing import Dict, Any

class GPTLayoutGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def generate_layout(self, prompt: str, image_base64: str = None, title: str = None, subtitle: str = None) -> Dict[str, Any]:
        """
        GPT-4oを使用してサムネイルレイアウトを生成
        
        Args:
            prompt: レイアウト生成のプロンプト
            image_base64: base64エンコードされた画像（任意）
            title: タイトル（フォールバック用）
            subtitle: サブタイトル（フォールバック用）
            
        Returns:
            レイアウト情報を含む辞書
        """
        
        system_prompt = """
        あなたはYouTubeサムネイルの専門デザイナーです。
        ユーザーが指定したタイトルとサブタイトルを必ず使用して、魅力的なレイアウトを作成してください。
        
        重要な制約:
        1. ユーザーが指定したタイトルとサブタイトルの文字列を一字一句変更せずに使用する
        2. 「YouTube」や「サムネイル」などの汎用的な文字は使用しない
        3. 画像は提供された向きを考慮して適切に配置する
        4. 文字は大きく、読みやすく配置する
        5. 背景とのコントラストを重視する
        
        必ず以下のJSON形式で応答してください。説明文や追加のテキストは一切含めないでください：

        {
          "background": {
            "type": "gradient",
            "gradientStart": "#カラーコード",
            "gradientEnd": "#カラーコード",
            "gradientDirection": "horizontal"
          },
          "elements": [
            {
              "type": "text",
              "role": "title",
              "content": "ユーザー指定のタイトルをそのまま",
              "x": 50,
              "y": 100,
              "fontSize": 72,
              "color": "#FFFFFF",
              "fontWeight": "bold",
              "alignment": "left",
              "stroke": {
                "color": "#000000",
                "width": 4
              }
            },
            {
              "type": "text", 
              "role": "subtitle",
              "content": "ユーザー指定のサブタイトルをそのまま",
              "x": 50,
              "y": 200,
              "fontSize": 36,
              "color": "#FFFF00",
              "fontWeight": "bold",
              "alignment": "left",
              "stroke": {
                "color": "#000000",
                "width": 3
              }
            },
            {
              "type": "image",
              "x": 700,
              "y": 150,
              "width": 400,
              "height": 400,
              "rotation": 0
            }
          ]
        }

        絶対に守ること:
        - 応答は上記のJSON形式のみ
        - 説明文や```json```のマークダウンは不要
        - ユーザーが指定したタイトルとサブタイトルを変更しない
        - title roleとsubtitle roleの両方のテキスト要素を必ず含める
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
                    {
                        "type": "text", 
                        "text": "この画像を参考にレイアウトを作成してください。人物の向きや表情を考慮して、最も魅力的に見える配置を選択してください。画像は回転せず、元の向きのまま使用してください。"
                    },
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
                max_tokens=2000,
                temperature=0.1  # より一貫した出力のため低く設定
            )
            
            response_text = response.choices[0].message.content
            print(f"GPTレスポンス（最初の200文字）: {response_text[:200] if response_text else 'None'}")
            
            if not response_text:
                print("エラー: GPTからの応答が空です")
                return self._get_fallback_layout(title, subtitle)
            
            response_text = response_text.strip()
            
            # JSONの抽出
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end == -1:
                    json_end = len(response_text)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                if json_end == -1:
                    json_end = len(response_text)
                response_text = response_text[json_start:json_end].strip()
            
            print(f"抽出されたJSON（最初の200文字）: {response_text[:200]}")
            
            if not response_text or response_text == "":
                print("エラー: JSON抽出後の文字列が空です")
                return self._get_fallback_layout(title, subtitle)
            
            # JSONの先頭と末尾を確認
            if not response_text.startswith('{'):
                # { の位置を探す
                brace_start = response_text.find('{')
                if brace_start != -1:
                    response_text = response_text[brace_start:]
                else:
                    print("エラー: JSONの開始が見つかりません")
                    return self._get_fallback_layout(title, subtitle)
            
            if not response_text.endswith('}'):
                # 最後の } の位置を探す
                brace_end = response_text.rfind('}')
                if brace_end != -1:
                    response_text = response_text[:brace_end + 1]
                else:
                    print("エラー: JSONの終了が見つかりません")
                    return self._get_fallback_layout(title, subtitle)
            
            layout_data = json.loads(response_text)
            
            # レイアウトデータの検証・補正
            layout_data = self._validate_and_fix_layout(layout_data)
            
            return layout_data
            
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"解析対象の文字列: '{response_text[:500] if 'response_text' in locals() else 'undefined'}'")
            return self._get_fallback_layout(title, subtitle)
        except Exception as e:
            print(f"GPT API呼び出しエラー: {e}")
            return self._get_fallback_layout(title, subtitle)
    
    def _validate_and_fix_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レイアウトデータの検証と修正
        """
        # デフォルト背景の設定
        if "background" not in layout_data:
            layout_data["background"] = {
                "type": "gradient",
                "gradientStart": "#FF6B6B",
                "gradientEnd": "#4ECDC4",
                "gradientDirection": "horizontal"
            }
        
        # 要素の検証
        if "elements" not in layout_data:
            layout_data["elements"] = []
        
        # title roleとsubtitle roleのテキストが存在するかチェック
        has_title = any(elem.get("role") == "title" for elem in layout_data["elements"] if elem.get("type") == "text")
        has_subtitle = any(elem.get("role") == "subtitle" for elem in layout_data["elements"] if elem.get("type") == "text")
        
        # 不足している場合は警告
        if not has_title:
            print("警告: タイトル要素が見つかりません")
        if not has_subtitle:
            print("警告: サブタイトル要素が見つかりません")
        
        for element in layout_data["elements"]:
            # 座標の境界チェック
            if "x" in element:
                element["x"] = max(0, min(element["x"], 1280))
            if "y" in element:
                element["y"] = max(0, min(element["y"], 720))
            
            # テキスト要素の検証
            if element.get("type") == "text":
                if "fontSize" not in element:
                    element["fontSize"] = 72 if element.get("role") == "title" else 36
                if "color" not in element:
                    element["color"] = "#FFFFFF"
                if "fontWeight" not in element:
                    element["fontWeight"] = "bold"
                if "alignment" not in element:
                    element["alignment"] = "left"
                
                # デフォルトの縁取り追加
                if "stroke" not in element:
                    element["stroke"] = {
                        "color": "#000000",
                        "width": 4 if element.get("role") == "title" else 3
                    }
            
            # 画像要素の検証
            if element.get("type") == "image":
                if "width" not in element:
                    element["width"] = 350
                if "height" not in element:
                    element["height"] = 350
                if "rotation" not in element:
                    element["rotation"] = 0  # 回転しない
        
        return layout_data
    
    def _get_fallback_layout(self, title: str = None, subtitle: str = None) -> Dict[str, Any]:
        """
        エラー時のフォールバックレイアウト
        """
        return {
            "background": {
                "type": "gradient",
                "gradientStart": "#FF6B6B",
                "gradientEnd": "#4ECDC4",
                "gradientDirection": "horizontal"
            },
            "elements": [
                {
                    "type": "text",
                    "role": "title",
                    "content": title or "この方法で再生数が10倍に！",
                    "x": 50,
                    "y": 100,
                    "fontSize": 72,
                    "color": "#FFFFFF",
                    "fontWeight": "bold",
                    "alignment": "left",
                    "stroke": {
                        "color": "#000000",
                        "width": 4
                    }
                },
                {
                    "type": "text",
                    "role": "subtitle", 
                    "content": subtitle or "必見！！",
                    "x": 50,
                    "y": 200,
                    "fontSize": 48,
                    "color": "#FFFF00",
                    "fontWeight": "bold",
                    "alignment": "left",
                    "stroke": {
                        "color": "#FF0000",
                        "width": 3
                    }
                },
                {
                    "type": "image",
                    "x": 700,
                    "y": 150,
                    "width": 400,
                    "height": 400,
                    "rotation": 0
                }
            ]
        }