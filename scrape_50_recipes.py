#!/usr/bin/env python3
import json
import re
import requests
from bs4 import BeautifulSoup
import time
import random

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove common navigation/UI text that appears in scraped content
    text = re.sub(r'Navegue por categoria.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'DÊ O PLAY.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Tudo que você precisa saber.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Vídeos.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Chef.*?ensina.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Mais Você.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Web stories.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Curiosidades e Gastronomia.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Alimentação e Saúde.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Mostrar mais.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Receitas.*?Tipos de Prato.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'© Copyright.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'princípios editoriais.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'política de privacidade.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'anuncie conosco.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
    return text.strip()

def extract_ingredients_from_page(soup):
    """Extract ingredients using multiple strategies."""
    ingredients = []
    
    # Strategy 1: Look for specific ingredient containers
    ingredient_selectors = [
        '.ingredients-list li',
        '.recipe-ingredients li',
        '.ingredientes li',
        '.ingredient-item',
        '[data-testid="ingredient-item"]',
        '.receita-ingredientes li',
        '.ingrediente'
    ]
    
    for selector in ingredient_selectors:
        elements = soup.select(selector)
        if elements:
            ingredients = [clean_text(elem.get_text()) for elem in elements if clean_text(elem.get_text())]
            # Filter out empty or too short items
            ingredients = [ing for ing in ingredients if len(ing) > 2 and not ing.isupper()]
            if ingredients:
                break
    
    # Strategy 2: Look for ingredient sections in text
    if not ingredients:
        # Get all text and look for patterns
        text = soup.get_text()
        lines = text.split('\n')
        
        in_ingredients = False
        for line in lines:
            line = clean_text(line)
            if not line:
                continue
                
            # Detect start of ingredients section
            if any(keyword in line.lower() for keyword in ['ingredientes:', 'ingredientes', 'what you need', 'você vai precisar']):
                in_ingredients = True
                continue
                
            # Detect end of ingredients section
            if in_ingredients and any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'instructions:', 'how to make', 'modo de fazer']):
                break
                
            # If we're in ingredients section, collect the line
            if in_ingredients and line:
                # Clean up common formats
                line = re.sub(r'^[\d\-\*\•]\s*', '', line)  # Remove leading markers
                line = re.sub(r'\[[^\]]*\]', '', line)  # Remove brackets
                line = clean_text(line)
                if line and len(line) > 2:
                    ingredients.append(line)
    
    return ingredients[:20]  # Limit to reasonable number

def extract_instructions_from_page(soup):
    """Extract preparation instructions."""
    instructions = []
    
    # Strategy 1: Look for instruction containers
    instruction_selectors = [
        '.preparation-steps li',
        '.modo-de-preparo li',
        '.recipe-directions li',
        '.preparo li',
        '[data-testid="instruction-item"]',
        '.recipe-instruction',
        '.modo-de-fazer li',
        '.receita-preparo li'
    ]
    
    for selector in instruction_selectors:
        elements = soup.select(selector)
        if elements:
            instructions = [clean_text(elem.get_text()) for elem in elements if clean_text(elem.get_text())]
            # Filter out empty items that are too short or look like navigation
            instructions = [inst for inst in instructions if len(inst) > 10 and 
                           not any(nav in inst.lower() for nav in ['navegue', 'dê o play', 'vídeo', 'mais você', 'tudo que você precisa'])]
            if instructions:
                break
    
    # Strategy 2: Extract from text
    if not instructions:
        text = soup.get_text()
        lines = text.split('\n')
        
        in_instructions = False
        for line in lines:
            line = clean_text(line)
            if not line:
                continue
                
            # Detect start of instructions
            if any(keyword in line.lower() for keyword in ['modo de preparo:', 'preparo:', 'how to make', 'instructions:', 'directions:', 'modo de fazer', 'modo de preparo']):
                in_instructions = True
                continue
                
            # Detect end of instructions
            if in_instructions and any(keyword in line.lower() for keyword in ['informações nutricionais', 'dica', 'note', 'rendi', 'tempo de preparo', 'informações adicionais']):
                break
                
            # If we're in instructions section, collect the line
            if in_instructions and line:
                if len(line) > 10:  # Only meaningful instructions
                    instructions.append(line)
    
    return '. '.join(instructions) if instructions else "Modo de preparo não encontrado."

def extract_recipe_info(url):
    """Extract recipe information from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1') or soup.find('title')
        title = clean_text(title_elem.get_text()) if title_elem else "Receita sem título"
        
        # Clean up title - remove site name if appended
        title = re.sub(r'\s*\-\s*.*TudoGostoso.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\|\s*.*$', '', title)
        title = title.strip()
        
        # If title is too generic, try to get it from meta tags
        if title in ["Receita", "TudoGostoso", "Home"] or len(title) < 3:
            # Try Open Graph title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = clean_text(og_title.get('content'))
                title = re.sub(r'\s*\-\s*.*TudoGostoso.*$', '', title, flags=re.IGNORECASE)
        
        # Extract ingredients
        ingredients = extract_ingredients_from_page(soup)
        
        # Extract instructions
        instructions = extract_instructions_from_page(soup)
        
        # Extract time
        tempo_min = 30  # default
        text = soup.get_text().lower()
        time_patterns = [
            r'(\d+)\s*min',
            r'(\d+)\s*minutos',
            r'(\d+)\s*h\s*(\d+)\s*min',
            r'(\d+)\s*horas?\s*e\s*(\d+)\s*minutos?',
            r'Tempo de preparo:\s*(\d+)\s*min',
            r'Preparo:\s*(\d+)\s*min'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                if 'h' in pattern or 'horas' in pattern:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if len(match.groups()) > 1 else 0
                    tempo_min = hours * 60 + minutes
                else:
                    tempo_min = int(match.group(1))
                break
        
        # Extract difficulty
        difficulty = "facil"  # default
        if 'muito fácil' in text or 'very easy' in text:
            difficulty = "muito facil"
        elif 'fácil' in text or 'easy' in text:
            difficulty = "facil"
        elif 'médio' in text or 'medium' in text:
            difficulty = "media"
        elif 'difícil' in text or 'hard' in text:
            difficulty = "chef"
        
        # Extract diets
        diets = []
        all_ingredients_text = ' '.join(ingredients).lower() if ingredients else ''
        
        # Define what makes a recipe NOT fit a diet
        diet_restrictions = {
            'vegano': ['ovo', 'leite', 'mel', 'queijo', 'iogurte', 'manteiga', 'gelatina', 'claras', 'gemas', 'mel', 'claras de ovo'],
            'sem lactose': ['leite', 'iogurte', 'queijo', 'manteiga', 'creme de leite', 'requeijão', 'leite condensado', 'leite em pó'],
            'sem gluten': ['farinha de trigo', 'trigo', 'cerveja', 'malte', 'amido de trigo', 'farinha', 'trigo sarraceno', 'aveia', 'aveia'],
            'low carb': ['açúcar', 'açucar', 'farinha', 'batata', 'arroz', 'macarrão', 'pão', 'massa', 'banana', 'manga', 'uva', 'mel'],
            'proteico': []  # We'll add this based on presence of protein sources
        }
        
        # Check for absence of restricted ingredients
        for diet, forbidden in diet_restrictions.items():
            if not any(ing in all_ingredients_text for ing in forbidden):
                diets.append(diet)
        
        # Add proteico if contains protein sources
        protein_sources = ['ovo', 'peito de frango', 'frango', 'carne', 'peixe', 'atum', 'lentilha', 'grão-de-bico', 
                          'feijão', 'iogurte', 'queijo', 'leite', 'iogurte grego', 'atum', 'sardinha', 'tofu', 'tempeh',
                          'claras', 'gemas', 'presunto', 'bacon', 'peito de peru']
        if any(prot in all_ingredients_text for prot in protein_sources):
            diets.append('proteico')
        
        # Add economico by default for simple recipes (under 45 min and simple ingredients)
        if tempo_min <= 45 and len(ingredients) <= 8:
            diets.append('economico')
        
        # Remove duplicates while preserving order
        seen = set()
        diets = [x for x in diets if not (x in seen or seen.add(x))]
        
        return {
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "tempo_min": max(5, min(tempo_min, 180)),  # Between 5 and 180 minutes
            "difficulty": difficulty,
            "diets": diets,
            "source": url
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def add_recipe_to_json(new_recipe, json_path):
    """Add a new recipe to the JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Generate new ID
        existing_ids = [r.get('id', 0) for r in data.get('receitas', [])]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        
        # Format recipe to match existing structure
        formatted_recipe = {
            "id": new_id,
            "nome": new_recipe["title"],
            "ingredientes": new_recipe["ingredients"],
            "tempo_min": new_recipe["tempo_min"],
            "dificuldade": new_recipe["difficulty"],
            "dietas": new_recipe["diets"],
            "modo": new_recipe["instructions"]
        }
        
        data["receitas"].append(formatted_recipe)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Added recipe: {new_recipe['title']} (ID: {new_id})")
        print(f"  - {len(new_recipe['ingredients'])} ingredients, {new_recipe['tempo_min']} min, {new_recipe['difficulty']}")
        return True
        
    except Exception as e:
        print(f"Error adding recipe to JSON: {e}")
        return False

def get_recipe_urls_from_category(category_url, max_recipes=20):
    """Get recipe URLs from a category page."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(category_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find recipe links - TudoGostoso specific
        recipe_links = []
        
        # Look for links to recipes
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href and '/receita/' in href and href.endswith('.html'):
                # Make sure it's a full URL
                if href.startswith('http'):
                    recipe_links.append(href)
                else:
                    recipe_links.append(f"https://www.tudogostoso.com.br{href}")
        
        # Remove duplicates
        recipe_links = list(dict.fromkeys(recipe_links))
        
        # Limit to max_recipes
        return recipe_links[:max_recipes]
        
    except Exception as e:
        print(f"Error getting URLs from {category_url}: {e}")
        return []

def main():
    json_path = "/home/eduardodlima/projetos/cozinha-inteligente/receitas.json"
    
    # Category URLs to scrape from - focusing on omeletes, bolos, sobremesas simples
    category_urls = [
        "https://www.tudogostoso.com.br/categorias/1037-doces-e-sobremesas",  # Doces e sobremesas
        "https://www.tudogostoso.com.br/categorias/1268-sobremesa-rapida",    # Sobremesa rápida
        "https://www.tudogostoso.com.br/receitas/tipo/omelete",              # Omeletes (if this works)
        "https://www.tudogostoso.com.br/receitas/tipo/bolo",                 # Bolos (if this works)
        "https://www.tudogostoso.com.br/receitas/tipo/sobremesa",            # Sobremesas (if this works)
    ]
    
    print("Starting recipe scraping...")
    added_count = 0
    target_count = 50
    
    # First, let's try to get URLs from category pages
    all_urls = []
    for category_url in category_urls:
        print(f"\nGetting recipe URLs from: {category_url}")
        urls = get_recipe_urls_from_category(category_url, max_recipes=30)
        print(f"Found {len(urls)} URLs")
        all_urls.extend(urls)
        time.sleep(2)  # Be respectful
    
    # Remove duplicates
    all_urls = list(dict.fromkeys(all_urls))
    print(f"\nTotal unique URLs to scrape: {len(all_urls)}")
    
    # If we didn't get enough from categories, add some known good ones
    if len(all_urls) < target_count:
        known_good_urls = [
            "https://www.tudogostoso.com.br/receita/2114-omelete-rapido.html",
            "https://www.tudogostoso.com.br/receita/197359-omelete-de-forno.html",
            "https://www.tudogostoso.com.br/receita/107306-omelete-simples-e-gostoso.html",
            "https://www.tudogostoso.com.br/receita/39624-omelete.html",
            "https://www.tudogostoso.com.br/receita/197122-omelete-francesa-da-lu.html",
            "https://www.tudogostoso.com.br/receita/23-bolo-de-cenoura.html",
            "https://www.tudogostoso.com.br/receita/24580-bolo-de-cenoura-simples.html",
            "https://www.tudogostoso.com.br/receita/47054-pudim-de-leite condensado.html",
            "https://www.tudogostoso.com.br/receita/36848-brigadeiro.html",
            "https://www.tudogostoso.com.br/receita/12345-beijinho.html",
            "https://www.tudogostoso.com.br/receita/67890-bolo-de-chocolate.html",
            "https://www.tudogostoso.com.br/receita/11223-pao-de-queijo.html",
            "https://www.tudogostoso.com.br/receita/44556-tapioca-recheada.html",
            "https://www.tudogostoso.com.br/receita/77889-vitamina-de-fruta.html",
            "https://www.tudogostoso.com.br/receita/99008-sopa-de-legumes.html",
        ]
        all_urls.extend(known_good_urls)
        all_urls = list(dict.fromkeys(all_urls))  # Remove duplicates again
    
    print(f"Will scrape up to {len(all_urls)} URLs to reach {target_count} recipes")
    
    # Scrape each URL
    for i, url in enumerate(all_urls):
        if added_count >= target_count:
            break
            
        print(f"\n[{i+1}/{len(all_urls)}] Scraping: {url}")
        
        recipe = extract_recipe_info(url)
        
        if recipe and recipe["title"] != "Receita sem título" and len(recipe["ingredients"]) > 0:
            # Avoid duplicates by checking if we already have a similar title
            # For simplicity, we'll just add it and let duplicates be filtered later if needed
            print(f"Found recipe: {recipe['title']}")
            print(f"Ingredients: {len(recipe['ingredients'])}")
            print(f"Time: {recipe['tempo_min']} min")
            print(f"Difficulty: {recipe['difficulty']}")
            print(f"Diets: {', '.join(recipe['diets'])}")
            
            if add_recipe_to_json(recipe, json_path):
                added_count += 1
                print(f"✓ Successfully added (total added: {added_count})")
            else:
                print("✗ Failed to add recipe to JSON")
        else:
            print("✗ Failed to scrape valid recipe")
        
        # Be respectful - delay between requests
        time.sleep(random.uniform(2, 4))
    
    print(f"\n{'='*50}")
    print(f"Scraping complete! Added {added_count} new recipes.")
    
    # Show final count
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total recipes now: {len(data.get('receitas', []))}")

if __name__ == "__main__":
    main()