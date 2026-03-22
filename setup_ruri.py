import os
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForFeatureExtraction, ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig

def main():
    model_id = "cl-nagoya/ruri-v3-30m"
    onnx_path = "ruri_30m_onnx"
    quantized_path = "ruri_30m_quantized"

    print(f"[LOG] 🚀 処理開始: {model_id} のダウンロードとONNX変換を行います。")

    # 1. HuggingFaceからダウンロード & ONNX(FP32)エクスポート
    print(f"[LOG] モデルをダウンロードし、{onnx_path} にエクスポート中...")
    try:
        model_ort = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model_ort.save_pretrained(onnx_path)
        tokenizer.save_pretrained(onnx_path)
        print("[LOG] ✅ ONNXエクスポートが完了しました。")
    except Exception as e:
        print(f"[ERROR] ONNXエクスポート中にエラーが発生しました: {e}")
        return

    # 2. Int8への量子化
    print(f"[LOG] 🔨 {quantized_path} へのInt8量子化を開始します...")
    try:
        quantizer = ORTQuantizer.from_pretrained(onnx_path, file_name="model.onnx")
        
        # Windowsの Intel Core / AMD Ryzen 向けに avx2 を指定して最適化します
        # (※Pi Zeroの場合は .arm64() でしたが、PC環境ではこちらが最速です)
        qconfig = AutoQuantizationConfig.avx2(is_static=False, per_channel=False)
        
        quantizer.quantize(save_dir=quantized_path, quantization_config=qconfig)
        tokenizer.save_pretrained(quantized_path)
        print("[LOG] ✅ 量子化が完了しました。")
    except Exception as e:
        print(f"[ERROR] 量子化中にエラーが発生しました: {e}")
        return

    # 3. 最終サイズの確認ログ
    try:
        size_bytes = sum(f.stat().st_size for f in os.scandir(quantized_path) if f.is_file())
        size_mb = size_bytes / (1024 * 1024)
        print(f"[LOG] 📦 最終モデルサイズ ('{quantized_path}' フォルダ): {size_mb:.2f} MB")
        
        if size_mb < 50:
            print("[LOG] 🎉 素晴らしい！モデルは50MB以下に収まりました。ノートPCでも爆速で動作します。")
            print(f"[LOG] 次のステップ: 生成された '{quantized_path}' フォルダを、メインスクリプトと同じディレクトリ（または対象プロジェクトのルート）に配置してください。")
    except Exception as e:
        print(f"[ERROR] フォルダサイズの計算中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()