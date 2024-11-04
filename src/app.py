import os
import argostranslate.package
import argostranslate.translate
from flask import Flask, jsonify, request
from flask_compress import Compress
from flask_caching import Cache
from dotenv import load_dotenv
load_dotenv()
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="stanza.models.tokenize.trainer")
api_key = os.getenv("API_KEY")

app = Flask(__name__)
cache = Cache(app=app, config={"CACHE_TYPE": "simple"})
Compress(app)
convertedText: list[dict[str, str]] = []

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal Server Error"}), 500

def install_package_if_needed(fr, to):
    available_local_packages = argostranslate.package.get_installed_packages()
    if not any(p.from_code == fr and p.to_code == to for p in available_local_packages):
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        try:
            p2i = next(filter(lambda x: x.from_code == fr and x.to_code == to, available_packages))
            argostranslate.package.install_from_path(p2i.download())
        except StopIteration:
            raise ValueError("Language conversion package is not available.")


@cache.cached(timeout=3600, key_prefix=lambda: f"{request.args.get('from')}_{request.args.get('to')}_{request.args.get('text')}")
@app.route("/translate", methods=["GET"])
def translate():
    global convertedText
    from_code = request.args.get("from")
    to_code = request.args.get("to")
    text = request.args.get("text")
    _api_key = request.args.get("api_key")
    if _api_key != api_key:
        return jsonify({"error": "Invalid API Key"}), 401
    try:
        install_package_if_needed(from_code, to_code)
    except Exception:
        return jsonify({"error": "Language Conversion is not available!"}), 500

    translatedText = argostranslate.translate.translate(text, from_code, to_code)
    convertedText.append({"from": from_code, "to": to_code, "text": text, "translatedText": translatedText})
    return jsonify({"translatedText": translatedText})

if os.getenv("ENV") == "dev":
    app.run(host="0.0.0.0", port=5000)
