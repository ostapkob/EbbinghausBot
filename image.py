# from google_images_download import google_images_download 
# response = google_images_download.googleimagesdownload()
# def hrefs_images(keyword ):
#     arguments = {
#                 "keywords": "",
#                 "limit":5,
#                 "format": "jpg",
#                 "size": ">400*300",
#                 "print_urls":True,
#                 "no_download": True
#                 }   #creating list of arguments
#     arguments['keywords'] = keyword
#     paths = response.download(arguments)   #passing the arguments to the function
#     return paths[0].values()

# if __name__ == "__main__":

#     print(hrefs_images('handle'))
black_list = ['https://www.collinsdictionary.com',
                'https://www.youtube.com']

a = 'https://www.youtube.com/watch?v=w2iOQtleNac&ab_channel=%D0%92%D0%B8%D0%BA%D1%82%D0%BE%D1%80%D0%A8%D0%B5%D0%BD%D0%B4%D0%B5%D1%80%D0%BE%D0%B2%D0%B8%D1%87'
for i in black_list:
    if a.startswith(i):
        print(i)
