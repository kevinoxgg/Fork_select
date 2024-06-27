from flask import Flask, request, jsonify
import boto3
import openai
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os

app = Flask(__name__)

# 初始化 AWS 客戶端
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3 = boto3.client('s3')
table = dynamodb.Table('UserInterests')

# 初始化 OpenAI 客戶端
openai.api_key = 'YOUR_OPENAI_API_KEY'

# 配置 S3 存儲桶名稱
bucket_name = 'your-s3-bucket-name'

@app.route('/')
def home():
    return "歡迎來到 Foresell AI 禮物推薦工具！"

@app.route('/profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    user_id = data.get('user_id')
    interests = data.get('interests')

    # 儲存用戶興趣到 DynamoDB
    table.put_item(
        Item={
            'user_id': user_id,
            'interests': interests
        }
    )

    return jsonify({"message": "用戶興趣已成功儲存"})

@app.route('/recommend', methods=['POST'])
def recommend_gifts():
    data = request.get_json()
    user_id = data.get('user_id')

    # 從 DynamoDB 獲取用戶興趣
    response = table.get_item(
        Key={
            'user_id': user_id
        }
    )

    if 'Item' not in response:
        return jsonify({"message": "未找到用戶興趣"})

    interests = response['Item']['interests']

    # 根據用戶興趣生成禮物推薦
    recommendations = generate_recommendations(interests)

    return jsonify({"recommendations": recommendations})

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    prompt = data.get('prompt')

    # 使用 OpenAI 生成回覆
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100
    )

    answer = response.choices[0].text.strip()
    return jsonify({"answer": answer})

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    # 假設 CSV 文件已上傳到 /mnt/data 路徑
    csv_file = '/mnt/data/文創圖 - giftu (1).csv'
    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        text = row['text_column_name']  # 替換為您的文本列名稱
        url = row['url_column_name']    # 替換為您的URL列名稱
        image_path = f"/mnt/data/image_{index}.png"
        
        create_image_with_text(text, url, image_path)
        upload_to_s3(image_path, bucket_name, f"images/image_{index}.png")
        
        # 刪除本地生成的圖片文件
        os.remove(image_path)

    return jsonify({"message": "圖片已生成並上傳到 S3。"})

def create_image_with_text(text, url, output_path):
    width, height = 800, 400
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)
    font_size = 20
    
    # 創建一個空白圖片
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)
    
    # 加載字體
    font = ImageFont.load_default()
    
    # 添加文本
    draw.text((10, 10), text, fill=text_color, font=font)
    draw.text((10, 50), url, fill=text_color, font=font)
    
    # 保存圖片
    image.save(output_path)

def upload_to_s3(file_path, bucket, object_name):
    s3.upload_file(file_path, bucket, object_name)

def generate_recommendations(interests):
    # 這是簡單的示例邏輯，您可以根據需求進行調整
    gifts = {
        '運動': ['籃球', '跑鞋', '運動手環'],
        '音樂': ['吉他', '耳機', '音樂會門票'],
        '書籍': ['小說', '科幻書籍', '歷史書籍']
    }

    recommended_gifts = []
    for interest in interests:
        if interest in gifts:
            recommended_gifts.extend(gifts[interest])

    return recommended_gifts

if __name__ == '__main__':
    app.run(debug=True)
