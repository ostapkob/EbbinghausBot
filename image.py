from google_images_download import google_images_download 
response = google_images_download.googleimagesdownload()
def hrefs_images(keyword ):
    arguments = {
                "keywords": "",
                "limit":5,
                "format": "jpg",
                "size": ">400*300",
                "print_urls":True,
                "no_download": True
                }   #creating list of arguments
    arguments['keywords'] = keyword
    paths = response.download(arguments)   #passing the arguments to the function
    return paths[0].values()

if __name__ == "__main__":

    print(hrefs_images('handle'))
