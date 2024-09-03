from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('query')
    response = process_query(user_input)
    return jsonify({'response': response})

def process_query(query):
    # Implement NLP processing here
    return "You asked: " + query

if __name__ == '__main__':
    app.run(debug=True)
