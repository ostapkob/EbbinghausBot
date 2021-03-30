from googletrans import Translator
from pymongo import MongoClient
from datetime import datetime
import time
import threading
from google_images_download import google_images_download 
from telegram.ext import CommandHandler
from config import token, logger, intervals, db_config, arguments
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
        logger.debug('--> translte')
        return translation.text

    def translate_from_target(self, word, target_langue=target_langue, native_langue=native_langue):
        word = word.lower()
        translation = self.translator.translate(word, dest=native_langue, src=target_langue)
        logger.debug(f'--> translte {translation.text}')
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
        logger.debug('--> audio')
        return audio

    def hrefs_images(self, keyword, steep=0):
        arguments['keywords'] = keyword
        paths = self.response.download(arguments)   #passing the arguments to the function
        href = self.check_hrefs(paths[0][keyword], steep)
        logger.debug(f'--> images {href}')
        return href

    def send_word(self, chat_id, word, steep ):
        target_word = self.translate_from_target(word) # TODO threding
        image = self.hrefs_images(word, steep)
        audio = self.get_audio(word)
        words = '#' + word + ' - ' + target_word
        logger.debug(f"steep {steep}")
        self.bot.send_photo(chat_id=chat_id,   
                            photo=image,
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

    def check_hrefs(self, hrefs, steep=0):
        """
        check hrefs by working from steep, if all href bad return None
        """
        for i in range(steep, len(hrefs)):
            try:
                requests.get(hrefs[i])
                return hrefs[i]
            except requests.ConnectionError:
                logger.error(f"{hrefs[i]} - bad request")
            except requests.exceptions.MissingSchema:
                logger.error(f"{hrefs[i]} - bad url")
        return 'https://translate.google.com'


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

['http://www.sncplastic.com/wp-content/uploads/Peek-Gear.jpg', 'https://www.3dnatives.com/en/wp-content/uploads/sites/2/PEEKcover.jpg', 'https://sc04.alicdn.com/kf/H2703494779a04883bf42fc5314171a60A.jpg', 'https://www.ensingerplastics.com/-/media/ensinger/images/shapes/product-groups/tubes-peek-elekem-1280x480px.ashx?as=1&la=en&h=480&w=1280&iar=1&hash=C066D4C7C231BBF3965DDDA4BEE68A67', 'https://cdn.shortpixel.ai/client/q_lossless,ret_img,w_500,h_333/https://www.asp-plastics.com/wp-content/uploads/2020/09/Dexnyl-PEEK-Film-Natural-500x333.jpg', 'https://top3dshop.ru/image/cache/data/products/materials/apium/apium_peek_450_1-500x500.jpg', 'https://www.roechling.com/fileadmin/media/Roechling-Industrial/Materials/images/PEEK-sheet-plate-rod-tubing-SUSTAPEEK.jpg']
print()