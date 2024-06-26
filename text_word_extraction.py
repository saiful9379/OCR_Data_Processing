

import os
import cv2
import fitz
import glob
import json
from pdf2image import convert_from_path
import numpy as np

DPI = 300
UNIT_CONSTANT = 72

def draw_region(text_data, image, file_name, output_dir = "logs/word_logs"):
    for page in text_data:
        # print(page)
        px1, py1, px2, py2 = page["x"], page["y"], page["x"]+page["w"], page["y"]+page["h"]
        lines = page["lines"]
            # print(page)
        if len(lines):
            for line in lines:
                lx1, ly1, lx2, ly2, text = line["x"], line["y"], line["x"]+line["w"], line["y"]+line["h"], line["text"]
                cv2.putText(image, str(text), (lx1, ly1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv2.LINE_AA)
                cv2.rectangle(image, pt1=(lx1, ly1),pt2=(lx2, ly2),color= (0,0,255),thickness=2)
    cv2.imwrite(os.path.join(output_dir, file_name), image)

def data_formate(bbox, text):
    x, y, w, h = bbox[0], bbox[1], abs(bbox[2]-bbox[0]), abs(bbox[3]-bbox[1]) 
    block= {
            "type": "block",
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "page": 1,
            "lines": [
                {
                    "type": "line",
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "page": 1,
                    "text": text
                }
            ]
        }
    return block


def block_region_format(bbox:dict={}, text:str="") ->dict:
    x, y, w, h = bbox[0], bbox[1], abs(bbox[2]-bbox[0]), abs(bbox[3]-bbox[1]) 
    region = {
        "shape_attributes": {
            "name": "rect",
            "x": x,
            "y": y,
            "width": w,
            "height": h
            },
        "region_attributes": {
                "layout": "Text",
                "text":text
            }
        }
    return region

def file_formate(file_name:str="", size :int= "")-> dict:
    file_structure = {
        "filename": file_name,
        "size": size,
        "regions": []
        }
    return file_structure

def pdf_to_image_conversion(pdf_file_path:str, DPI:int)-> str:
    """
    Discription: this function use pdf to image conversion
    Parameters:
        pdf_file_path {str} : input pdf file path
        logs_dir{dir}       : log path directory
        image_name {str}    : image name from pdf file
    Returns: None
    
    """
    images = convert_from_path(pdf_file_path, DPI)
    images = [np.array(image) for image in images]
    return images


def text_extraction(pdf_file, file_name="unknown"):
    page_data = {}
    with fitz.open(pdf_file) as document:
        for page_number, page in enumerate(document):
            # print(page)
            data_list = []
            words = page.getText("words")
            for word in words:
                if len(word)< 5:
                    # print(word)
                    continue
                bbox =[round((i/UNIT_CONSTANT)*DPI) for i in word[:4]]
                text = word[4].replace(u'\xa0', ' ')
                formated_data = block_region_format(bbox, text)
                # print(formated_data)
                # formated_data = data_formate(bbox, text)
                data_list.append(formated_data)
            page_data[f"{file_name}_{page_number}.jpg"] = data_list

    return page_data

def data_extraction_vgg_format(pdf_file, img_path, data_dict):
    images = pdf_to_image_conversion(pdf_file, DPI)

    text_extracted_data = text_extraction(
        pdf_file, 
        file_name = os.path.basename(pdf_file)[:-4]
        )
    cnt = 0
    for key, value in text_extracted_data.items():
        image = images[cnt]
        output_file_path = os.path.join(img_path, key)
        cv2.imwrite(output_file_path, image)
        # os.getsize
        size = os.path.getsize(output_file_path)
        # print(value)
        print(size)
        file_key = f'{key}{size}'
        file_structure = file_formate(file_name=key, size=size)
        print(file_structure)
        for block in value:
            # print("===", block)
        #     for line in block["lines"]:
        #         # region = region_format(line)
                file_structure["regions"].append(block)
        data_dict[file_key] = file_structure
        cnt+=1
    

    return data_dict

if __name__ =="__main__":
    pdf_dir = "data/r1"
    img_path ="logs/images"
    pdf_files = glob.glob(pdf_dir+"/*.pdf")
    os.makedirs(img_path, exist_ok= True)
    data_dict = {}
    for pdf_file in pdf_files:
        data_dict = data_extraction_vgg_format(pdf_file, img_path, data_dict)
    with open('logs/vgg_extracted.json', 'w', encoding ='utf8') as json_file:
        json.dump(data_dict, json_file, ensure_ascii = False, indent=4)
