from python_worker.config import get_shared_config
from python_worker.services.scraper_gateway import ScraperGateway

config = get_shared_config()
gateway = ScraperGateway(config, None)
filenames = gateway.save_images(["https://ireland.apollo.olxcdn.com/v1/files/eyJmbiI6IjA0Mm5pb3g2Zmpuay1BUEwiLCJ3IjpbeyJmbiI6ImVudmZxcWUxYXk0azEtQVBMIiwicyI6IjE2IiwiYSI6IjAiLCJwIjoiMTAsLTEwIn1dfQ.K_aIEeHPTqJjm-WOK4wbKEWIBTIfdgSjveeUjTFrh1g.webp"], "oto", "4BPpw")
print("returned filenames:", filenames)
