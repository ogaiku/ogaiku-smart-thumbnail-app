from PIL import Image, ImageDraw, ImageFont
import os
import math
import platform
from typing import Dict, Any, Tuple

class ThumbnailRenderer:
    def __init__(self):
        self.canvas_size = (1280, 720)
        self.default_font_size = 48
        self.japanese_fonts = self._get_japanese_fonts()
        
    def _get_japanese_fonts(self) -> list:
        """システムに応じた日本語フォントパスを取得"""
        system = platform.system()
        fonts = []
        
        if system == "Windows":
            fonts = [
                'C:/Windows/Fonts/NotoSansCJK-Regular.ttc',
                'C:/Windows/Fonts/YuGothM.ttc',
                'C:/Windows/Fonts/YuGothB.ttc',
                'C:/Windows/Fonts/meiryo.ttc',
                'C:/Windows/Fonts/meiryob.ttc',
                'C:/Windows/Fonts/msgothic.ttc',
                'C:/Windows/Fonts/msmincho.ttc',
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/arialbd.ttf'
            ]
        elif system == "Darwin":  # macOS
            fonts = [
                '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
                '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Arial.ttf'
            ]
        else:  # Linux
            fonts = [
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/takao-gothic/TakaoGothic.ttf',
                '/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            ]
        
        return fonts
        
    def render_thumbnail(self, layout_data: Dict[str, Any], user_image: Image.Image = None) -> Image.Image:
        """
        レイアウトデータに基づいてサムネイル画像を生成
        """
        # キャンバス作成
        canvas = Image.new('RGB', self.canvas_size, color='white')
        draw = ImageDraw.Draw(canvas)
        
        # 背景描画
        self._draw_background(canvas, draw, layout_data.get('background', {}))
        
        # 要素描画
        elements = layout_data.get('elements', [])
        
        # 画像要素を先に描画（テキストが上に来るように）
        for element in elements:
            if element.get('type') == 'image' and user_image:
                self._draw_image(canvas, element, user_image)
        
        # テキスト要素を後で描画
        for element in elements:
            if element.get('type') == 'text':
                self._draw_text_with_effects(draw, element)
        
        return canvas
    
    def _draw_background(self, canvas: Image.Image, draw: ImageDraw.Draw, bg_data: Dict[str, Any]):
        """背景を描画"""
        bg_type = bg_data.get('type', 'solid')
        
        if bg_type == 'solid':
            color = bg_data.get('color', '#FFFFFF')
            draw.rectangle([0, 0, self.canvas_size[0], self.canvas_size[1]], fill=color)
        
        elif bg_type == 'gradient':
            start_color = bg_data.get('gradientStart', '#FFFFFF')
            end_color = bg_data.get('gradientEnd', '#000000')
            direction = bg_data.get('gradientDirection', 'horizontal')
            self._draw_gradient(draw, start_color, end_color, direction)
    
    def _draw_gradient(self, draw: ImageDraw.Draw, start_color: str, end_color: str, direction: str = 'horizontal'):
        """グラデーション背景を描画"""
        try:
            start_rgb = self._hex_to_rgb(start_color)
            end_rgb = self._hex_to_rgb(end_color)
            
            if direction == 'horizontal':
                for x in range(self.canvas_size[0]):
                    ratio = x / self.canvas_size[0]
                    r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                    g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                    b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                    draw.line([(x, 0), (x, self.canvas_size[1])], fill=(r, g, b))
            
            elif direction == 'vertical':
                for y in range(self.canvas_size[1]):
                    ratio = y / self.canvas_size[1]
                    r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                    g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                    b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                    draw.line([(0, y), (self.canvas_size[0], y)], fill=(r, g, b))
            
            elif direction == 'diagonal':
                diagonal_length = math.sqrt(self.canvas_size[0]**2 + self.canvas_size[1]**2)
                for x in range(self.canvas_size[0]):
                    for y in range(self.canvas_size[1]):
                        distance = math.sqrt(x**2 + y**2)
                        ratio = distance / diagonal_length
                        ratio = min(1.0, ratio)
                        
                        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                        draw.point((x, y), fill=(r, g, b))
                        
        except Exception as e:
            print(f"グラデーション描画エラー: {e}")
            draw.rectangle([0, 0, self.canvas_size[0], self.canvas_size[1]], fill=start_color)
    
    def _draw_text_with_effects(self, draw: ImageDraw.Draw, text_data: Dict[str, Any]):
        """エフェクト付きテキストを描画"""
        try:
            content = text_data.get('content', '')
            x = text_data.get('x', 0)
            y = text_data.get('y', 0)
            font_size = text_data.get('fontSize', self.default_font_size)
            color = text_data.get('color', '#000000')
            font_weight = text_data.get('fontWeight', 'normal')
            alignment = text_data.get('alignment', 'left')
            stroke_data = text_data.get('stroke', {})
            
            print(f"テキスト描画: '{content}' (role: {text_data.get('role', 'unknown')})")
            
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
            
            # 縁取り描画
            stroke_color = stroke_data.get('color', '#000000')
            stroke_width = stroke_data.get('width', 0)
            
            if stroke_width > 0:
                # より太い縁取りのために範囲を拡張
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx*dx + dy*dy <= stroke_width*stroke_width:
                            draw.text((x + dx, y + dy), content, font=font, fill=stroke_color)
            
            # メインテキスト描画
            draw.text((x, y), content, font=font, fill=color)
            
            print(f"テキスト描画完了: '{content}' at ({x}, {y})")
            
        except Exception as e:
            print(f"テキスト描画エラー: {e}")
            print(f"テキスト内容: {content}")
    
    def _draw_image(self, canvas: Image.Image, img_data: Dict[str, Any], user_image: Image.Image):
        """画像を描画（回転なし、元の向きを保持）"""
        try:
            x = img_data.get('x', 0)
            y = img_data.get('y', 0)
            width = img_data.get('width', 300)
            height = img_data.get('height', 300)
            
            print(f"画像描画開始: サイズ({width}, {height})")
            
            # 画像の縦横比を保持してリサイズ
            original_ratio = user_image.width / user_image.height
            target_ratio = width / height
            
            if original_ratio > target_ratio:
                # 幅を基準にリサイズ
                new_width = width
                new_height = int(width / original_ratio)
            else:
                # 高さを基準にリサイズ
                new_height = height
                new_width = int(height * original_ratio)
            
            # 回転は一切しない
            resized_image = user_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 配置位置の調整（指定された位置に配置）
            final_x = x
            final_y = y
            
            # 境界チェック
            final_x = max(0, min(final_x, self.canvas_size[0] - resized_image.width))
            final_y = max(0, min(final_y, self.canvas_size[1] - resized_image.height))
            
            print(f"画像配置完了: 位置({final_x}, {final_y}) サイズ({resized_image.width}, {resized_image.height})")
            
            # 透過画像の場合はアルファ合成
            if resized_image.mode == 'RGBA':
                canvas.paste(resized_image, (final_x, final_y), resized_image)
            else:
                canvas.paste(resized_image, (final_x, final_y))
                
        except Exception as e:
            print(f"画像描画エラー: {e}")
    
    def _get_font(self, size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
        """日本語対応フォントを取得"""
        try:
            # 太字の場合は太字フォントを優先
            font_candidates = self.japanese_fonts.copy()
            
            if weight == 'bold':
                bold_fonts = [f for f in font_candidates if any(keyword in f.lower() for keyword in ['bold', 'b.ttc', 'gothic', 'ゴシック'])]
                font_candidates = bold_fonts + font_candidates
            
            # 日本語フォントを優先的に試行
            for font_path in font_candidates:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        # 日本語文字でテスト
                        test_text = "テスト"
                        temp_img = Image.new('RGB', (100, 100))
                        temp_draw = ImageDraw.Draw(temp_img)
                        temp_draw.text((0, 0), test_text, font=font, fill='black')
                        print(f"使用フォント: {font_path}")
                        return font
                    except Exception as e:
                        print(f"フォント読み込み失敗: {font_path} - {e}")
                        continue
            
            # Noto Sansを試行
            try:
                noto_paths = [
                    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf',
                    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                    'C:/Windows/Fonts/NotoSansCJK-Regular.ttc'
                ]
                
                for noto_path in noto_paths:
                    if os.path.exists(noto_path):
                        return ImageFont.truetype(noto_path, size)
                
            except Exception as e:
                print(f"Noto Sansフォント読み込み失敗: {e}")
            
            # 最終手段: デフォルトフォント
            print("デフォルトフォントを使用します")
            return ImageFont.load_default()
            
        except Exception as e:
            print(f"フォント取得エラー: {e}")
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """16進数カラーコードをRGBタプルに変換"""
        try:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return (0, 0, 0)