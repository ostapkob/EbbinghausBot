from googletrans import Translator
from pymongo import MongoClient
from datetime import datetime
import time
import threading
from google_images_download import google_images_download 
from telegram.ext import CommandHandler
from config import token, logger, intervals, db_config, arguments, black_list
from telegram.ext import Updater, MessageHandler, Filters
from gtts import gTTS
import telegram
import requests
import os

class TranslateBot(Updater):
    translator = Translator()
    native_langue = 'ru'
    target_langue = 'en'
    intervals = intervals
    arguments = arguments
    mongo_client = MongoClient(db_config['HOST'])
    mongodb = mongo_client[db_config['DB']]
    collection = mongodb[db_config['colection']]
    response = google_images_download.googleimagesdownload()

    def add_to_db(self, chat_id, word):
        word = word.lower()
        if self.collection.find_one({'word':word, 'chat_id': chat_id}):
            return False
        with self.mongo_client:
            obj = {'word': word, 'steep': 1, 'chat_id': chat_id, 'timestamp' : datetime.utcnow() + self.intervals[1] }
        self.collection.insert_one(obj)
        return True
    
    def update_item_db(self, chat_id, word):
        with self.mongo_client:
            obj = self.collection.find_one({'word':word, 'chat_id': chat_id})
        if obj:
            updated = obj.copy()
            updated['steep']+=1
            updated['timestamp'] += self.intervals[updated['steep']]
            new_obj = {'$set': updated}
            self.collection.update_one(obj, new_obj)
            if obj['steep'] > 5:
                logger.info('delete '+ chat_id + ' ' + word)
                self.collection.delete_one({'word':word, 'chat_id': chat_id})
            return True
        print('No')
        return False

    def delete_to_db(self, chat_id, word):
        word = word.lower()
        obj = self.collection.find_one({'word' : word, 'chat_id': chat_id})
        if obj:
            self.collection.delete_one(obj)
            return True
        return False

    def translate_to_target(self, word, target_langue=target_langue, native_langue=native_langue):
        translation = self.translator.translate(word, dest=target_langue, src=native_langue)
        logger.debug('translte--> ')
        return translation.text

    def translate_from_target(self, word, target_langue=target_langue, native_langue=native_langue):
        word = word.lower()
        translation = self.translator.translate(word, dest=native_langue, src=target_langue)
        logger.debug(f'--------------{word}--------------------')
        logger.debug(f'translte --> {translation.text}')
        return translation.text

    def change_target_langue(self, target_langue):
        self.target_langue = target_langue

    def change_native_langue(self, native_langue):
        self.native_langue = native_langue
    
    def get_audio(self, word, remove_file=True, target_langue=target_langue):
        audio=gTTS(text=word, lang=target_langue, slow='False')
        audio.save(word+'.ogg')
        audio = open(word+'.ogg', 'rb')
        if remove_file:
            os.remove(word + '.ogg')
        logger.debug('audio -->')
        return audio

    def hrefs_images(self, keyword, steep=0):
        arguments['keywords'] = keyword
        paths = self.response.download(arguments)   #passing the arguments to the function
        href = self.check_hrefs(paths[0][keyword], steep)
        logger.debug(f'images --> {href}')
        return href

    def send_word(self, chat_id, word, steep ):
        target_word = self.translate_from_target(word) # TODO threding and quite
        image = self.hrefs_images(word, steep)
        audio = self.get_audio(word)
        words = '#' + word + ' - ' + target_word
        logger.debug(f"steep {steep}")
        try:
            self.bot.send_photo(chat_id=chat_id,   
                                photo=image,
                                caption=words)
        except telegram.error.BadRequest:
            self.bot.send_message(chat_id=chat_id,
                                  text=words)
        except telegram.error.NetworkError:
            logger.error(f'====Error Network====')
        try:
            self.bot.send_audio(chat_id=chat_id,
                                audio=audio,
                                caption=words)
        except telegram.error.NetworkError:
            logger.error(f'====Error Network====')

    def revise_db(self): 
        while True:
            logger.info(str(datetime.utcnow()))
            with self.mongo_client:
                obj = self.collection.find({'timestamp': {'$lte': datetime.utcnow()}})
            for user in obj:
                thred_send_word = threading.Thread(target=self.send_word, args=(user['chat_id'], user['word'], user['steep']))
                thred_send_word.start()
                # self.send_word(user['chat_id'], user['word'], user['steep'])
                self.update_item_db(user['chat_id'], user['word'])
            time.sleep(60)

    def start_listen(self):
        th = threading.Thread(target=self.revise_db)
        th.start()

    def check_hrefs(self, hrefs, steep=0):
        """
        check hrefs by working from steep, if all hrefs bad return None
        """
        logger.info(hrefs)
        logger.info(steep)
        for i in range(steep, len(hrefs)):
            logger.info(hrefs[i])
            for site in black_list:
                if hrefs[i].startswith(site):
                    logger.info('BLACK LIST', hrefs[i])
                    i +=1
            try:
                requests.get(hrefs[i])
                return hrefs[i]
            except requests.ConnectionError:
                logger.error(f"{hrefs[i]} - bad request")
            except requests.exceptions.MissingSchema:
                logger.error(f"{hrefs[i]} - bad url")
        return 'https://translate.google.com'


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a EbbinghausBot, sent me word")

def echo(update, context):
    chat_id = update.effective_chat.id
    message = update.message.text.lower()
    if message[0] == ".":
        if updater.delete_to_db(chat_id, message[1:]):
            updater.bot.send_message(chat_id=chat_id,   
                                text= "I delete this word")
        else:
            updater.bot.send_message(chat_id = chat_id,
                                text="I didn't find this word")
    else:
        updater.send_word(chat_id, message, steep=0)
        if not updater.add_to_db(chat_id, message):
            updater.bot.send_message(chat_id = chat_id,
                                text="I already know this word")

updater = TranslateBot(token=token)
start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

dispatcher = updater.dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)

if __name__ == "__main__":
    updater.start_listen()
    updater.start_polling()
