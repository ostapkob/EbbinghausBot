from googletrans import Translator
from pymongo import MongoClient
from datetime import datetime
from datetime import timedelta
import time
import threading
from google_images_download import google_images_download 
from telegram.ext import CommandHandler
from config import token, logger, intervals, db_config, arguments
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters
from google_images_download import google_images_download 
from gtts import gTTS
import telegram
import os
# updater = Updater(token=token)

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

    # def __init__(self, intervals, db_config):
    #     self.intervals = intervals 
    #     self.mongo_client = MongoClient(db_config['HOST'])
    #     self.mongodb = self.mongo_client[db_config['DB']]
    #     self.collection = self.mongodb[db_config['colection']]
        
    def add_to_db(self, chat_id, word):
        word = word.lower()
        if self.collection.find_one({'word':word, 'chat_id': chat_id}):
            return False
        with self.mongo_client:
            obj = {'word': word, 'steep': 0, 'chat_id': chat_id, 'timestamp' : datetime.utcnow() }
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
                logger.info('delite '+ chat_id + ' ' + word)
                self.collection.delete_one({'word':word, 'chat_id': chat_id})
            return True
        print('No')
        return False

    def translate_to_target(self, word, target_langue=target_langue, native_langue=native_langue):
        translation = self.translator.translate(word, dest=target_langue, src=native_langue)
        return translation.text

    def translate_from_target(self, word, target_langue=target_langue, native_langue=native_langue):
        word = word.lower()
        translation = self.translator.translate(word, dest=native_langue, src=target_langue)
        return translation.text

    def change_target_langue(self, target_langue):
        self.target_langue = target_langue

    def change_native_langue(self, native_langue):
        self.native_langue = native_langue
    
    def get_audio(self, word, target_langue=target_langue):
        audio=gTTS(text=word, lang=target_langue, slow='False')
        audio.save(word+'.ogg')
        audio = open(word+'.ogg', 'rb')
        os.remove(word + '.ogg')
        return audio

    def hrefs_images(self, keyword):
        arguments['keywords'] = keyword
        paths = self.response.download(arguments)   #passing the arguments to the function
        return paths[0][keyword]

    def send_word(self, chat_id, word, steep ):
        words = '#' + word + ' - ' + self.translate_from_target(word) # TODO threding
        images = self.hrefs_images(word)
        audio = self.get_audio(word)
        logger.debug(steep)
        try:
            self.bot.send_photo(chat_id=chat_id,   
                                photo=images[steep-1],
                                caption=words)
        except telegram.error.BadRequest:
            logger.error(steep)
            self.bot.send_photo(chat_id=chat_id,   
                                photo=images[steep],
                                caption=words)
        self.bot.send_audio(chat_id=chat_id,
                            audio=audio,
                            caption=words)

    def check_out_db(self): 
        logger.info(str(datetime.utcnow()))
        with self.mongo_client:
            obj = self.collection.find({'timestamp': {'$lte': datetime.utcnow()}})
        for user in obj:
            self.send_word(user['chat_id'], user['word'], user['steep'])
            self.update_item_db(user['chat_id'], user['word'])
        time.sleep(50)
        self.check_out_db()

    def listen(self):
        th = threading.Thread(target=self.check_out_db)
        th.start()


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def echo(update, context):
    updater.send_word(update.effective_chat.id, update.message.text, steep=1)
    updater.add_to_db(update.effective_chat.id, update.message.text)
    updater.update_item_db(update.effective_chat.id, update.message.text)

updater = TranslateBot(token=token)

start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)

dispatcher = updater.dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)

if __name__ == "__main__":
    updater.listen()
    updater.start_polling()

