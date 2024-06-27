from flask import Flask, request, jsonify
import boto3
import openai

app = Flask(__name__)

# 初始化 AWS 客戶端
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('UserInterests')

# 初始化 OpenAI 客戶端
openai.api_key = 'YOUR_OPENAI_API_KEY'

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
