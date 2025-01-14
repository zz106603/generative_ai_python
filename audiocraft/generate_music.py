from flask import Flask, request, jsonify
import threading
import os
from audiocraft.models import MusicGen

app = Flask(__name__)

# 작업 상태 저장 (간단한 딕셔너리로 구현)
tasks = {}
STATIC_FOLDER = "static"
os.makedirs(STATIC_FOLDER, exist_ok=True)

# MusicGen 모델 로드 (비용이 큰 작업이므로 전역적으로 로드)
print("Loading MusicGen model...")
model = MusicGen.get_pretrained("medium")  # 'small', 'large' 옵션 가능
print("MusicGen model loaded.")

def generate_music(task_id, text_prompt, duration):
    try:
        # 작업 중 상태로 설정
        tasks[task_id] = {"status": "processing", "file_path": None}

        # MusicGen으로 음악 생성
        model.set_generation_params(duration=duration)
        audio_output = model.generate(text_prompt)

        # 생성된 파일 저장
        file_path = os.path.join(STATIC_FOLDER, f"generated_music_{task_id}.wav")
        model.save_wav(audio_output[0], file_path)

        # 작업 완료 상태로 업데이트
        tasks[task_id] = {"status": "completed", "file_path": file_path}
        print(f"Music generation completed for task {task_id}: {file_path}")

    except Exception as e:
        tasks[task_id] = {"status": "error", "message": str(e)}
        print(f"Error in task {task_id}: {e}")

@app.route('/generate-music', methods=['POST'])
def generate_music_api():
    try:
        data = request.json
        text_prompt = data.get("text", ["a relaxing piano melody"])  # 기본 프롬프트
        duration = data.get("duration", 10)  # 기본 지속 시간

        # 작업 ID 생성
        task_id = str(len(tasks) + 1)

        # 비동기로 작업 실행
        threading.Thread(target=generate_music, args=(task_id, text_prompt, duration)).start()

        # 즉시 응답 반환
        file_url = f"/static/generated_music_{task_id}.wav"
        return jsonify({"status": "accepted", "task_id": task_id, "file_url": file_url}), 202

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check-task/<task_id>', methods=['GET'])
def check_task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify(task)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
