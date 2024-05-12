from flask import Flask, request
from openai import OpenAI
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import json
import telebot  # tg
from bs4 import BeautifulSoup  # parse
import urllib.request, urllib.error, urllib.parse  # parse
import psycopg2  # db
import validators  # parse

api_key = "sk-proj-qA13jP53JQiolPEHN6hdT3BlbkFJQfzEKebA2y0Agl0tCcQX"
client = OpenAI(
    organization="org-v9LYQUdhWHat6hBF1NqXcec2",
    project="proj_Rs1ebsLfTT5yChmHJrSBrGuM",
    api_key=api_key,
)
bot_token = "6008734284:AAH_pmlVu1UpGGMUtlNdhEKulubVgOep56o"
resultsUsed = 5


conn = psycopg2.connect(
    database="bedivere",
    host="host.docker.internal",
    user="postgres",
    password="helloWorld200@",
    port="5432",
)
cursor = conn.cursor()

bot = telebot.TeleBot(bot_token)
data = {}

chroma_client = chromadb.PersistentClient(path="./chroma_db")
ebedmodel = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-ada-002", api_key=api_key
)

collection = chroma_client.get_or_create_collection(
    name="merlin", embedding_function=ebedmodel
)

app = Flask(__name__)


@bot.message_handler(commands=["start"])
def lgbt(message):
    if getOrgKeyByUser(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "Вітання, я бачу, Ви вже належите до організації, бажаєте щось дізнатись?",
            parse_mode="HTML",
        )
        if isAdmin(message.from_user.id):
            bot.send_message(
                message.chat.id,
                "Як очільнику можу відкрити вам таємницю команди /parse, кажуть, викликавши її в комбінації з посиланням я довідаюсь все про Вашу веб сторінку.",
                parse_mode="HTML",
            )
    else:
        bot.send_message(
            message.chat.id,
            "Вітання, я бачу, Ви ще не є частиною організації, щоб приєднатись, натисніть сюди -> /login",
            parse_mode="HTML",
        )


def respond(message, sender):
    context = "; ".join(
        collection.query(
            query_texts=[message],
            n_results=resultsUsed,
            where={"source": sender},
            include=["documents"],
        )["documents"][0]
    )
    # return json.dumps(context)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Ти асистент компанії, відповідай на питання згідно з контекстом, якщо відповідь з нього не випливає то необхідно перепросити і повідомити користувача про це. Контекст: "
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


def add(data, sender, id):
    collection.add(documents=[data], metadatas=[{"source": sender}], ids=[id])


@app.route("/add", methods=["POST"])
def rec():
    decoded = request.json
    if decoded:
        message = decoded.get("data")
        sender = decoded.get("sender")
        id = decoded.get("id")
        if message:
            add(message, sender, id)
            return "Good"
    return "Bad"

def getOrgKeyByUser(userid):
    cursor.execute("SELECT (orgkey) FROM Users WHERE username=%s", (str(userid),))
    res = cursor.fetchone()
    if res:
        return res[0]
    return False


def isAdmin(userid):
    cursor.execute("SELECT (admin) FROM Users WHERE username='%s'", (userid,))
    return cursor.fetchone()


def loginUser(message):
    cursor.execute("SELECT * FROM Organisations WHERE key=%s", (message.text,))
    orgExists = len(cursor.fetchall()) > 0
    if orgExists:
        if not isAdmin(message.from_user.id):
            cursor.execute(
                "INSERT INTO Users (username, admin, orgkey) VALUES (%s, %s, %s)",
                (message.from_user.id, False, message.text),
            )
            conn.commit()

        bot.send_message(message.chat.id, "Успішно зареєстровано")
    else:
        bot.send_message(message.chat.id, "Ключ не правильний")


@bot.message_handler(commands=["login"])
def lgbt(message):
    msg = bot.send_message(
        message.chat.id,
        "Введіть ключ доступу. Якщо у вас немає ключа доступу і ви бажаєте зареєструвати свою організацію, зверніться до @Merlin_morder_admin_bot",
    )
    bot.register_next_step_handler(msg, loginUser)

def parse(message, link):
    to_parse = [link]
    parsed = {}
    progress = bot.send_message(
        message.chat.id, str(len(parsed)) + "/" + str(len(to_parse))
    )
    for curlink in to_parse:
        try:
            html_doc = urllib.request.urlopen(curlink)
            soup = BeautifulSoup(html_doc, "html.parser")
            links = [link.get("href").split("#")[0] for link in soup.find_all("a")]
            for l in links:
                if l not in to_parse and validators.url(l):
                    to_parse.append(l)
            parsed[curlink] = soup.text
        except:
            parsed[curlink] = ("error",)
        finally:
            try:
                percent = len(parsed) / len(to_parse) * 10
                bar = "["
                for i in range(10):
                    if i < percent:
                        bar += "="
                    else:
                        bar += "  "
                bar += "]"
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=progress.id,
                    text=str(len(parsed)) + "/" + str(len(to_parse)) + "\n" + bar,
                )
            except:
                a = 0
    return parsed

@bot.message_handler(commands=["parse"])
def lgbt(message):
    if(len(message.text.split(' '))<2):
        bot.send_message(message.chat.id, "Введіть інформацчію у форматі '/parse https://example.com'")
    
    data[message.chat.id] = parse(message=message, link=message.text.split(' ')[1])
    msg = bot.send_message(
        message.chat.id,
        "Чи бажаєте ви щоб ці сторінки були опрацьовані? Це коштуватиме вам "
        + str(len(data[message.chat.id]))
        + "грн. (так/ні)",
    )
    bot.register_next_step_handler(msg, lookThrough)


def lookThrough(message):
    if message.text == "так" or message.text == "Так":
        org = getOrgKeyByUser(message.from_user.id)

        i = 1
        for inf in data[message.chat.id]:
            info = data[message.chat.id][inf][0]
            add(info, org, inf)
            i += 1
    data[message.chat.id] = None


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(
        message,
        respond(message=message.text, sender=getOrgKeyByUser(message.from_user.id)),
    )


api = False


def startAPI():
    app.run(debug=True, host="0.0.0.0", port=1357)


if api:
    startAPI()
else:
    bot.infinity_polling()
