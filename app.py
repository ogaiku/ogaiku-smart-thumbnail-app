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
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

def init_session_state():
    """セッション状態の初期化"""
    if 'generated_thumbnail' not in st.session_state:
        st.session_state.generated_thumbnail = None
    if 'current_layout' not in st.session_state:
        st.session_state.current_layout = None
    if 'processed_image' not in st.session_state:
        st.session_state.processed_image = None
    if 'openai_key' not in st.session_state:
        # .envから読み込み、なければ空文字
        st.session_state.openai_key = os.getenv("OPENAI_API_KEY", "")
    if 'remove_bg_key' not in st.session_state:
        # .envから読み込み、なければ空文字
        st.session_state.remove_bg_key = os.getenv("REMOVE_BG_API_KEY", "")

def image_to_base64(image):
    """PIL画像をbase64エンコードに変換"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def create_enhanced_prompt(title, subtitle, design_style, color_theme):
    """より詳細で制約の厳しいプロンプトを作成"""
    prompt = f"""
    YouTubeサムネイルのレイアウトを作成してください。

    【絶対に使用するテキスト】
    - メインタイトル: 「{title}」
    - サブタイトル: 「{subtitle}」

    【重要】上記のタイトルとサブタイトルの文字列を一字一句変更せずに使用してください。
    「YouTube」「サムネイル」などの汎用的な文字は追加しないでください。

    【デザイン要件】
    - デザインスタイル: {design_style}
    - カラーテーマ: {color_theme}
    - サムネイルサイズ: 1280x720px

    【レイアウト要件】
    1. タイトル「{title}」を大きなフォント（70-90px）で目立つ位置に配置
    2. サブタイトル「{subtitle}」を中程度のフォント（35-50px）でタイトルの近くに配置
    3. 人物画像は元の向きのまま使用（回転しない）
    4. 文字には必ず縁取りを付けて視認性を確保
    5. 背景は鮮やかで目を引く色合い

    【文字の視認性】
    - 白文字に黒縁取り（幅3-5px）または黒文字に白縁取り
    - フォントは太字（bold）
    - 背景とのコントラストを十分に確保

    必ずJSON形式で、title roleとsubtitle roleの両方のテキスト要素を含めてください。
    """
    return prompt

def validate_api_keys(openai_key, remove_bg_key):
    """APIキーの有効性をチェック"""
    errors = []
    
    if not openai_key or openai_key.startswith("sk-your-") or len(openai_key.strip()) == 0:
        errors.append("有効なOpenAI APIキーを入力してください")
    
    if not remove_bg_key or remove_bg_key.startswith("your-remove-bg") or len(remove_bg_key.strip()) == 0:
        errors.append("有効なRemove.bg APIキーを入力してください")
    
    return errors

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
        
        # .envファイルの状態を表示
        env_openai = os.getenv("OPENAI_API_KEY", "")
        env_remove_bg = os.getenv("REMOVE_BG_API_KEY", "")
        
        if env_openai and not env_openai.startswith("sk-your-"):
            st.success(f"OpenAI APIキーが.envから読み込まれました")
        if env_remove_bg and not env_remove_bg.startswith("your-remove-bg"):
            st.success(f"Remove.bg APIキーが.envから読み込まれました")
        
        # セッション状態からAPIキーを取得
        openai_key = st.text_input(
            "OpenAI API Key", 
            value=st.session_state.openai_key,
            type="password",
            help="sk-で始まるAPIキーを入力してください (.envファイルから自動読み込み)"
        )
        
        remove_bg_key = st.text_input(
            "Remove.bg API Key", 
            value=st.session_state.remove_bg_key,
            type="password",
            help="Remove.bgのAPIキーを入力してください (.envファイルから自動読み込み)"
        )
        
        # APIキー更新
        if st.button("APIキーを更新"):
            st.session_state.openai_key = openai_key
            st.session_state.remove_bg_key = remove_bg_key
            st.success("APIキーが更新されました")
        
        # APIキー検証
        api_errors = validate_api_keys(openai_key, remove_bg_key)
        if api_errors:
            for error in api_errors:
                st.error(error)
        else:
            st.success("APIキー設定完了")
        
        # プレビュー設定
        st.subheader("プレビュー設定")
        show_layout_info = st.checkbox("レイアウト情報を表示", value=False)
        show_debug_info = st.checkbox("デバッグ情報を表示", value=False)
        
        # デバッグ情報表示
        if show_debug_info:
            st.subheader("環境変数デバッグ")
            st.write("現在の作業ディレクトリ:", os.getcwd())
            st.write(".envファイルの存在:", os.path.exists(".env"))
            if os.path.exists(".env"):
                st.write(".envファイルのサイズ:", os.path.getsize(".env"), "bytes")
            
            # 環境変数の状態（マスク済み）
            openai_env = os.getenv("OPENAI_API_KEY", "未設定")
            remove_bg_env = os.getenv("REMOVE_BG_API_KEY", "未設定")
            
            if openai_env != "未設定":
                st.write("OPENAI_API_KEY:", openai_env[:10] + "..." if len(openai_env) > 10 else openai_env)
            else:
                st.write("OPENAI_API_KEY: 未設定")
                
            if remove_bg_env != "未設定":
                st.write("REMOVE_BG_API_KEY:", remove_bg_env[:10] + "..." if len(remove_bg_env) > 10 else remove_bg_env)
            else:
                st.write("REMOVE_BG_API_KEY: 未設定")
    
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
        
        # アップロードされた画像のプレビュー
        if uploaded_file:
            original_image = Image.open(uploaded_file)
            st.image(original_image, caption="アップロードされた画像", width=300)
        
        # テキスト入力
        st.subheader("テキスト設定")
        title_text = st.text_input(
            "メインタイトル", 
            value="この方法で再生数が10倍に！",
            placeholder="魅力的なタイトルを入力"
        )
        subtitle_text = st.text_input(
            "サブタイトル", 
            value="必見！！",
            placeholder="補助テキストを入力（任意）"
        )
        
        # デザイン設定
        st.subheader("デザイン設定")
        design_style = st.selectbox(
            "デザインの雰囲気",
            ["インパクト重視", "ポップ", "プロフェッショナル", "シンプル", "エネルギッシュ", "エレガント"]
        )
        
        color_theme = st.selectbox(
            "カラーテーマ",
            ["レッド・オレンジ系", "ブルー・ティール系", "グリーン・ライム系", "パープル・ピンク系", "イエロー・オレンジ系", "モノクロ・ハイコントラスト"]
        )
        
        # 詳細オプション
        with st.expander("詳細オプション"):
            layout_preference = st.selectbox(
                "レイアウトの好み",
                ["バランス重視", "テキスト重視", "画像重視", "ダイナミック"]
            )
            text_position = st.selectbox(
                "テキスト配置",
                ["自動選択", "左側", "右側", "上部", "下部", "中央"]
            )
        
        # 生成ボタン
        generate_button = st.button("サムネイル生成", type="primary", use_container_width=True)
        
        if generate_button:
            # APIキーの検証
            api_errors = validate_api_keys(st.session_state.openai_key, st.session_state.remove_bg_key)
            if api_errors:
                st.error("APIキーを正しく設定してください")
                for error in api_errors:
                    st.error(error)
                return
            
            if uploaded_file and title_text:
                with st.spinner("サムネイルを生成中..."):
                    try:
                        # 画像の前処理
                        original_image = Image.open(uploaded_file)
                        
                        # 背景除去
                        st.info("背景を除去しています...")
                        bg_remover = BackgroundRemover(st.session_state.remove_bg_key)
                        processed_image = bg_remover.remove_background(original_image)
                        st.session_state.processed_image = processed_image
                        
                        # GPTによるレイアウト生成
                        st.info("AIがレイアウトを生成しています...")
                        layout_generator = GPTLayoutGenerator(st.session_state.openai_key)
                        
                        # 詳細プロンプト作成
                        enhanced_prompt = create_enhanced_prompt(title_text, subtitle_text, design_style, color_theme)
                        
                        # レイアウト配置の追加指示
                        if layout_preference != "バランス重視":
                            enhanced_prompt += f"\n\nレイアウト傾向: {layout_preference}"
                        if text_position != "自動選択":
                            enhanced_prompt += f"\nテキスト配置: {text_position}"
                        
                        layout_data = layout_generator.generate_layout(
                            enhanced_prompt, 
                            image_to_base64(processed_image),
                            title_text,
                            subtitle_text
                        )
                        st.session_state.current_layout = layout_data
                        
                        # サムネイル生成
                        st.info("最終画像を生成しています...")
                        renderer = ThumbnailRenderer()
                        thumbnail = renderer.render_thumbnail(layout_data, processed_image)
                        st.session_state.generated_thumbnail = thumbnail
                        
                        st.success("サムネイル生成完了！")
                        
                    except Exception as e:
                        st.error(f"エラーが発生しました: {str(e)}")
                        if show_debug_info:
                            st.exception(e)
            else:
                st.warning("画像とタイトルを入力してください")
    
    with col2:
        st.header("生成結果")
        
        if st.session_state.generated_thumbnail:
            # サムネイル表示
            st.image(st.session_state.generated_thumbnail, caption="生成されたサムネイル", use_container_width=True)
            
            # ダウンロードボタン
            buffer = io.BytesIO()
            st.session_state.generated_thumbnail.save(buffer, format='PNG')
            buffer.seek(0)
            
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.download_button(
                    label="PNGダウンロード",
                    data=buffer.getvalue(),
                    file_name=f"thumbnail_{uuid.uuid4().hex[:8]}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            with col2_2:
                # JPEGダウンロードも追加
                jpeg_buffer = io.BytesIO()
                rgb_image = st.session_state.generated_thumbnail.convert('RGB')
                rgb_image.save(jpeg_buffer, format='JPEG', quality=95)
                jpeg_buffer.seek(0)
                
                st.download_button(
                    label="JPEGダウンロード",
                    data=jpeg_buffer.getvalue(),
                    file_name=f"thumbnail_{uuid.uuid4().hex[:8]}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            # レイアウト情報表示
            if show_layout_info and st.session_state.current_layout:
                with st.expander("レイアウト情報"):
                    st.json(st.session_state.current_layout)
            
            # 再調整機能
            st.subheader("レイアウト再調整")
            
            # プリセット調整オプション
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                quick_adjustments = st.selectbox(
                    "クイック調整",
                    ["カスタム", "文字を大きく", "文字を小さく", "画像を大きく", "画像を小さく", "より鮮やかに", "よりシンプルに"]
                )
            
            with col3_2:
                if st.button("クイック調整実行"):
                    if quick_adjustments != "カスタム":
                        quick_adjustment_prompt = f"""
                        現在のレイアウトを「{quick_adjustments}」の指示に従って調整してください。
                        タイトル: {title_text}
                        サブタイトル: {subtitle_text}
                        """
                        
                        with st.spinner("レイアウトを調整中..."):
                            try:
                                layout_generator = GPTLayoutGenerator(st.session_state.openai_key)
                                new_layout = layout_generator.generate_layout(
                                    quick_adjustment_prompt,
                                    image_to_base64(st.session_state.processed_image)
                                )
                                st.session_state.current_layout = new_layout
                                
                                renderer = ThumbnailRenderer()
                                new_thumbnail = renderer.render_thumbnail(new_layout, st.session_state.processed_image)
                                st.session_state.generated_thumbnail = new_thumbnail
                                
                                st.success("クイック調整完了！")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"調整中にエラーが発生しました: {str(e)}")
            
            # カスタム調整
            adjustment_text = st.text_area(
                "詳細な調整指示",
                placeholder="例: タイトルをもっと中央に、文字を赤色に、画像を右上に移動してください",
                height=100
            )
            
            if st.button("カスタム調整実行", use_container_width=True) and adjustment_text:
                with st.spinner("レイアウトを再調整中..."):
                    try:
                        layout_generator = GPTLayoutGenerator(st.session_state.openai_key)
                        
                        # 現在のレイアウトと調整指示を含むプロンプト
                        adjustment_prompt = f"""
                        現在のレイアウト情報: {json.dumps(st.session_state.current_layout)}
                        
                        タイトル: {title_text}
                        サブタイトル: {subtitle_text}
                        
                        調整指示: {adjustment_text}
                        
                        上記の調整指示に従ってレイアウトを修正してください。
                        必ずタイトルとサブタイトルの内容は変更せず、位置や見た目のみ調整してください。
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
                        if show_debug_info:
                            st.exception(e)
        else:
            st.info("左側でコンテンツを入力してサムネイルを生成してください")
            
            # サンプル画像表示
            st.subheader("サンプル")
            st.write("こんなサムネイルが生成できます：")
            
            sample_info = """
            **機能:**
            - AI自動レイアウト生成
            - 背景自動除去
            - 多彩なデザインスタイル
            - リアルタイム調整
            - モバイル対応表示
            """
            st.markdown(sample_info)

if __name__ == "__main__":
    main()