import streamlit as st
import os
from PIL import Image
import io
import base64
import uuid
from gpt_layout import GPTLayoutGenerator
from remove_bg import BackgroundRemover
from image_renderer import ThumbnailRenderer
import json

# 環境変数の設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-your-openai-api-key-here")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY", "your-remove-bg-api-key-here")

def init_session_state():
    """セッション状態の初期化"""
    if 'generated_thumbnail' not in st.session_state:
        st.session_state.generated_thumbnail = None
    if 'current_layout' not in st.session_state:
        st.session_state.current_layout = None
    if 'processed_image' not in st.session_state:
        st.session_state.processed_image = None

def image_to_base64(image):
    """PIL画像をbase64エンコードに変換"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def main():
    st.set_page_config(
        page_title="AI YouTube Thumbnail Generator",
        page_icon="🎨",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("AI YouTube Thumbnail Generator")
    st.write("AIが自動でYouTubeサムネイルのレイアウトを生成します")
    
    # サイドバーでの設定
    with st.sidebar:
        st.header("設定")
        
        # APIキー設定
        st.subheader("APIキー")
        openai_key = st.text_input("OpenAI API Key", value=OPENAI_API_KEY, type="password")
        remove_bg_key = st.text_input("Remove.bg API Key", value=REMOVE_BG_API_KEY, type="password")
        
        if st.button("APIキーを更新"):
            os.environ["OPENAI_API_KEY"] = openai_key
            os.environ["REMOVE_BG_API_KEY"] = remove_bg_key
            st.success("APIキーが更新されました")
    
    # メインコンテンツエリア
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("コンテンツ入力")
        
        # 画像アップロード
        uploaded_file = st.file_uploader(
            "人物・アイコン画像をアップロード",
            type=['png', 'jpg', 'jpeg'],
            help="背景が自動で除去されます"
        )
        
        # テキスト入力
        title_text = st.text_input("タイトル", placeholder="メインタイトルを入力")
        subtitle_text = st.text_input("サブタイトル", placeholder="補助テキストを入力（任意）")
        
        # デザイン設定
        st.subheader("デザイン設定")
        design_style = st.selectbox(
            "デザインの雰囲気",
            ["ポップ", "シンプル", "インパクト重視", "プロフェッショナル", "カジュアル"]
        )
        
        color_theme = st.selectbox(
            "カラーテーマ",
            ["赤系", "青系", "緑系", "黄色系", "紫系", "オレンジ系", "モノクロ"]
        )
        
        # 生成ボタン
        if st.button("サムネイル生成", type="primary"):
            if uploaded_file and title_text:
                with st.spinner("サムネイルを生成中..."):
                    try:
                        # 画像の前処理
                        original_image = Image.open(uploaded_file)
                        
                        # 背景除去
                        bg_remover = BackgroundRemover(remove_bg_key)
                        processed_image = bg_remover.remove_background(original_image)
                        st.session_state.processed_image = processed_image
                        
                        # GPTによるレイアウト生成
                        layout_generator = GPTLayoutGenerator(openai_key)
                        
                        # プロンプト作成
                        prompt = f"""
                        以下の情報でYouTubeサムネイルのレイアウトを作成してください：
                        - タイトル: {title_text}
                        - サブタイトル: {subtitle_text}
                        - デザインスタイル: {design_style}
                        - カラーテーマ: {color_theme}
                        
                        サムネイルサイズ: 1280x720px
                        """
                        
                        layout_data = layout_generator.generate_layout(
                            prompt, 
                            image_to_base64(processed_image)
                        )
                        st.session_state.current_layout = layout_data
                        
                        # サムネイル生成
                        renderer = ThumbnailRenderer()
                        thumbnail = renderer.render_thumbnail(layout_data, processed_image)
                        st.session_state.generated_thumbnail = thumbnail
                        
                        st.success("サムネイル生成完了！")
                        
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
            else:
                st.warning("画像とタイトルを入力してください")
    
    with col2:
        st.header("生成結果")
        
        if st.session_state.generated_thumbnail:
            # サムネイル表示
            st.image(st.session_state.generated_thumbnail, caption="生成されたサムネイル")
            
            # ダウンロードボタン
            buffer = io.BytesIO()
            st.session_state.generated_thumbnail.save(buffer, format='PNG')
            buffer.seek(0)
            
            st.download_button(
                label="PNGダウンロード",
                data=buffer.getvalue(),
                file_name=f"thumbnail_{uuid.uuid4().hex[:8]}.png",
                mime="image/png"
            )
            
            # 再調整機能
            st.subheader("レイアウト再調整")
            adjustment_text = st.text_area(
                "調整指示を入力",
                placeholder="例: もっと中央寄りに、文字を大きく、色を変更してください"
            )
            
            if st.button("再調整実行") and adjustment_text:
                with st.spinner("レイアウトを再調整中..."):
                    try:
                        layout_generator = GPTLayoutGenerator(openai_key)
                        
                        # 現在のレイアウトと調整指示を含むプロンプト
                        adjustment_prompt = f"""
                        現在のレイアウト: {json.dumps(st.session_state.current_layout)}
                        調整指示: {adjustment_text}
                        
                        上記の調整指示に従ってレイアウトを修正してください。
                        """
                        
                        new_layout = layout_generator.generate_layout(
                            adjustment_prompt,
                            image_to_base64(st.session_state.processed_image)
                        )
                        st.session_state.current_layout = new_layout
                        
                        # 新しいサムネイル生成
                        renderer = ThumbnailRenderer()
                        new_thumbnail = renderer.render_thumbnail(new_layout, st.session_state.processed_image)
                        st.session_state.generated_thumbnail = new_thumbnail
                        
                        st.success("レイアウト調整完了！")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"調整中にエラーが発生しました: {str(e)}")
        else:
            st.info("左側でコンテンツを入力してサムネイルを生成してください")

if __name__ == "__main__":
    main()