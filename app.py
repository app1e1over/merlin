from flask import Flask, request
from openai import OpenAI
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json
import mysql.connector
import telebot
from threading import Thread, Lock

# mySQLdb = mysql.connector.connect(
#     host="localhost", user="root", password="ayK@r@mb@Bl1at", database="merlin"
# )
api_key = "sk-proj-qA13jP53JQiolPEHN6hdT3BlbkFJQfzEKebA2y0Agl0tCcQX"
client = OpenAI(
    organization="org-v9LYQUdhWHat6hBF1NqXcec2",
    project="proj_Rs1ebsLfTT5yChmHJrSBrGuM",
    api_key=api_key,
)
bot_token = "6008734284:AAH_pmlVu1UpGGMUtlNdhEKulubVgOep56o"


bot = telebot.TeleBot(bot_token)

# mycursor = mySQLdb.cursor()

# try:
#     mycursor.execute("SELECT * FROM users WHERE name='n'")
# except ():
#     mycursor.execute(
#         "CREATE TABLE users (name VARCHAR(100), email VARCHAR(40), password VARCHAR(255), keyword VARCHAR(255))"
#     )


resultsUsed = 5


chroma_client = chromadb.PersistentClient(path="./chroma_db")
ebedmodel = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-ada-002", api_key=api_key
)

collection = chroma_client.get_or_create_collection(
    name="lyceumUZH", embedding_function=ebedmodel
)

app = Flask(__name__)


def respond(message, sender):
    context = "; ".join(
        collection.query(
            query_texts=[message],
            n_results=resultsUsed,
            where={"source": sender},
            include=["documents"],
        )["documents"][0]
    )
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Ти про-український вчитель, відповідай на питання згідно з контекстом. Контекст: "
                + context,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )
    return completion.choices[0].message.content


@app.route("/message", methods=["POST"])
def resp():
    decoded = request.json
    if decoded:
        message = decoded.get("message")
        sender = decoded.get("sender")
        if message:
            return respond(message=message, sender=sender)

@app.route("/add", methods=["POST"])
def rec():
    decoded = request.json
    if decoded:
        message = decoded.get("data")
        sender = decoded.get("sender")
        id = decoded.get("id")
        if message:
            collection.add(
                documents=[message], metadatas=[{"source": sender}], ids=[id]
            )
            return "Good"
    return "Bad"


@app.route("/count")
def count():
    return str(collection.count())


@app.route("/peek")
def peek():
    return json.dumps(collection.peek()['documents'])


def getOrgByUser(username):
    return "Lyceum"

@bot.message_handler(commands=['login'])
def lgbt(message):
    bot.reply_to(message, message.text.split(" ")[1]+" is with pass " + message.text.split(" ")[2])

# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, respond(message.text, getOrgByUser(message.from_user)))



api = False
def startBot():
    bot.infinity_polling()
        

def startAPI():
    app.run(debug=True, host="0.0.0.0", port=1357)

if api:
    startAPI()
else:
    startBot()
