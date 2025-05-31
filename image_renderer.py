from PIL import Image, ImageDraw, ImageFont
import os
from typing import Dict, Any, Tuple

class ThumbnailRenderer:
    def __init__(self):
        self.canvas_size = (1280, 720)
        self.default_font_size = 48
        
    def render_thumbnail(self, layout_data: Dict[str, Any], user_image: Image.Image = None) -> Image.Image:
        """
        レイアウトデータに基づいてサムネイル画像を生成
        
        Args:
            layout_data: GPTから生成されたレイアウトデータ
            user_image: ユーザーがアップロードした画像
            
        Returns:
            生成されたサムネイル画像
        """
        # キャンバス作成
        canvas = Image.new('RGB', self.canvas_size, color='white')
        draw = ImageDraw.Draw(canvas)
        
        # 背景描画
        self._draw_background(canvas, draw, layout_data.get('background', {}))
        
        # 要素描画
        elements = layout_data.get('elements', [])
        for element in elements:
            if element.get('type') == 'text':
                self._draw_text(draw, element)
            elif element.get('type') == 'image' and user_image:
                self._draw_image(canvas, element, user_image)
        
        return canvas
    
    def _draw_background(self, canvas: Image.Image, draw: ImageDraw.Draw, bg_data: Dict[str, Any]):
        """
        背景を描画
        """
        bg_type = bg_data.get('type', 'solid')
        
        if bg_type == 'solid':
            color = bg_data.get('color', '#FFFFFF')
            draw.rectangle([0, 0, self.canvas_size[0], self.canvas_size[1]], fill=color)
        
        elif bg_type == 'gradient':
            start_color = bg_data.get('gradientStart', '#FFFFFF')
            end_color = bg_data.get('gradientEnd', '#000000')
            self._draw_gradient(draw, start_color, end_color)
    
    def _draw_gradient(self, draw: ImageDraw.Draw, start_color: str, end_color: str):
        """
        グラデーション背景を描画
        """
        try:
            # 色をRGBに変換
            start_rgb = self._hex_to_rgb(start_color)
            end_rgb = self._hex_to_rgb(end_color)
            
            # 水平グラデーション
            for x in range(self.canvas_size[0]):
                ratio = x / self.canvas_size[0]
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                
                draw.line([(x, 0), (x, self.canvas_size[1])], fill=(r, g, b))
                
        except Exception as e:
            print(f"グラデーション描画エラー: {e}")
            # フォールバック: 単色背景
            draw.rectangle([0, 0, self.canvas_size[0], self.canvas_size[1]], fill=start_color)
    
    def _draw_text(self, draw: ImageDraw.Draw, text_data: Dict[str, Any]):
        """
        テキストを描画
        """
        try:
            content = text_data.get('content', '')
            x = text_data.get('x', 0)
            y = text_data.get('y', 0)
            font_size = text_data.get('fontSize', self.default_font_size)
            color = text_data.get('color', '#000000')
            font_weight = text_data.get('fontWeight', 'normal')
            alignment = text_data.get('alignment', 'left')
            
            # フォント設定
            font = self._get_font(font_size, font_weight)
            
            # テキストサイズ計算
            bbox = draw.textbbox((0, 0), content, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # アライメント調整
            if alignment == 'center':
                x = x - text_width // 2
            elif alignment == 'right':
                x = x - text_width
            
            # 境界チェック
            x = max(0, min(x, self.canvas_size[0] - text_width))
            y = max(0, min(y, self.canvas_size[1] - text_height))
            
            # テキスト描画
            draw.text((x, y), content, font=font, fill=color)
            
        except Exception as e:
            print(f"テキスト描画エラー: {e}")
    
    def _draw_image(self, canvas: Image.Image, img_data: Dict[str, Any], user_image: Image.Image):
        """
        画像を描画
        """
        try:
            x = img_data.get('x', 0)
            y = img_data.get('y', 0)
            width = img_data.get('width', 300)
            height = img_data.get('height', 300)
            
            # 画像リサイズ
            resized_image = user_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # 境界チェック
            x = max(0, min(x, self.canvas_size[0] - width))
            y = max(0, min(y, self.canvas_size[1] - height))
            
            # 透過画像の場合はアルファ合成
            if resized_image.mode == 'RGBA':
                canvas.paste(resized_image, (x, y), resized_image)
            else:
                canvas.paste(resized_image, (x, y))
                
        except Exception as e:
            print(f"画像描画エラー: {e}")
    
    def _get_font(self, size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
        """
        フォントオブジェクトを取得
        """
        try:
            # システムフォントを試行
            font_paths = [
                # Windows
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/arialbd.ttf',
                # macOS
                '/System/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Arial Bold.ttf',
                # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            ]
            
            # 太字の場合は太字フォントを優先
            if weight == 'bold':
                bold_fonts = [path for path in font_paths if 'bold' in path.lower() or 'bd' in path.lower()]
                font_paths = bold_fonts + font_paths
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            
            # フォールバック: デフォルトフォント
            return ImageFont.load_default()
            
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        16進数カラーコードをRGBタプルに変換
        """
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return (0, 0, 0)  # フォールバック: 黒
    
    def add_border(self, image: Image.Image, border_width: int = 2, border_color: str = '#000000') -> Image.Image:
        """
        画像に枠線を追加
        """
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # 枠線描画
            for i in range(border_width):
                draw.rectangle([i, i, width-1-i, height-1-i], outline=border_color)
            
            return image
        except Exception as e:
            print(f"枠線追加エラー: {e}")
            return image