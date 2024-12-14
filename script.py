import xml.etree.ElementTree as ET
import requests
import csv
import json
from flask import Flask, Response, jsonify
import re

app = Flask(__name__)

@app.route('/') 
def fetch_data_xml():
    try:
        response = requests.get('https://api.geekdo.com/xmlapi/collection/megtrinity')
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f'Erreur lors de l\'appel API : {e}')
        return None
    

    
@app.route('/games')
def games():
    xml_data = fetch_data_xml()
    boardgames = data_boardgames_xml(xml_data)
    boardgames_list = []
    for game in boardgames:
        game_dict = {
            "id": game[0],
            'lst_published_year': game[1],
            'players' : game[3],
            'playtime' : game[4],
            'thumbnail' : game[5],
            'title' : game[2]
        }
        boardgames_list.append(game_dict)
    
    return Response(json.dumps(boardgames_list), mimetype='application/json')

@app.route('/games/<int:game_id>')
def get_game(game_id):
    try:
        response = requests.get(f'https://api.geekdo.com/xmlapi/boardgame/{game_id}')
        contents = response.content
    except requests.exceptions.RequestException as e:
        print(f'Erreur lors de l\'appel API : {e}')
        return None
    
    root = ET.fromstring(contents)
    game_info = []
    
    for item in root.findall('boardgame'):
        id_game = item.get('objectid')
        title = item.find('name').text
        year = item.find('yearpublished').text
        image = item.find('image').text
        description = item.find('description').text
        clean = re.compile('<.*?>')
        description_clean = re.sub(clean, '', description)
        min_player = item.find('minplayers').text
        max_player = item.find('maxplayers').text
        min_playtime = item.find('minplaytime').text
        max_playtime = item.find('maxplaytime').text
        
        categories = []
        for boardgame in item.findall('boardgamecategory'):
            categories.append(boardgame.text)
            
        expansions = []
        for boardgameexpansion in item.findall('boardgameexpansion'):
            expansions.append(boardgameexpansion.text)
        
        
        num_players = f'{min_player}-{max_player}' if min_player != max_player else min_player
        play_time = f'{min_playtime}min-{max_playtime}min' if min_playtime != max_playtime else f'{min_playtime}min'
        
        game_info.append({
            'id' : id_game, 
            'title' : title, 
            'description' : description_clean, 
            'image' : image, 
            'players' : num_players,
            'playtime' : play_time, 
            'categories' : ','.join(categories), 
            'expansions' : expansions})
        
    return jsonify(game_info)
    
    
def data_boardgames_xml(xml_data):
    root = ET.fromstring(xml_data)
    boardgames = []
    
    for item in root.findall('item'):
        id = item.get('objectid')
        title = item.find('name').text
        year = item.find('yearpublished').text
        thumbnail = item.find('thumbnail').text
        stats = item.find('stats')
        min_player = stats.get('minplayers')
        max_player = stats.get('maxplayers')
        min_playtime = stats.get('minplaytime')
        max_playtime = stats.get('maxplaytime')
        
        rating = stats.find('rating')
        average_value = rating.find('average')
        average = round(float(average_value.get('value')))
        
        
        num_players = f'{min_player}-{max_player}' if min_player != max_player else min_player
        play_time = f'{min_playtime}min-{max_playtime}min' if min_playtime != max_playtime else f'{min_playtime}min'
        
        boardgames.append([id, year, title, num_players, play_time, thumbnail])
        
    return boardgames

def write_to_csv(boardgames, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwritter = csv.writer(csvfile, delimiter=';')
        csvwritter.writerow(['ID','PUBLISHED YEAR', 'TITLE', 'NUMBER PLAYER', 'PLAY TIME', 'AVERAGE', 'THUMBNAIL'])
        for game in boardgames:
            csvwritter.writerow(game)

xml_data = fetch_data_xml()

if xml_data:
    boardgames = data_boardgames_xml(xml_data)
    write_to_csv(boardgames, 'boardgames.csv')
    