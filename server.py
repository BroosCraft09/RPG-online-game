#!/usr/bin/env python3
"""
RPG Game Server - FULL FEATURED
Dengan: PVP, Shop, Guild, Quest, Skill, Dungeon, Daily Rewards
Simpan sebagai: server.py
Jalankan: python server.py
"""

import socket
import threading
import json
import time
import random
import os
import pickle
from datetime import datetime

class GameDatabase:
    def __init__(self):
        self.players_file = 'players_data.pkl'
        self.lock = threading.Lock()
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.players_file):
            try:
                with open(self.players_file, 'rb') as f:
                    self.players = pickle.load(f)
                print(f"[DB] Loaded {len(self.players)} players")
            except:
                self.players = {}
        else:
            self.players = {}
    
    def save_player(self, player_data):
        with self.lock:
            self.players[player_data['name']] = player_data
            try:
                with open(self.players_file, 'wb') as f:
                    pickle.dump(self.players, f)
            except Exception as e:
                print(f"[DB ERROR] {e}")
    
    def get_player(self, name):
        return self.players.get(name)
    
    def player_exists(self, name):
        return name in self.players

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.db = GameDatabase()
        self.clients = {}
        self.init_game_data()
        
    def init_game_data(self):
        self.monsters = {
            'goblin': {'hp': 30, 'atk': 5, 'def': 2, 'exp': 15, 'gold': 10, 'loot': ['Health Potion', 'Goblin Dagger']},
            'orc': {'hp': 50, 'atk': 8, 'def': 4, 'exp': 25, 'gold': 20, 'loot': ['Iron Sword', 'Health Potion']},
            'troll': {'hp': 80, 'atk': 12, 'def': 6, 'exp': 40, 'gold': 35, 'loot': ['Steel Sword', 'Troll Ring']},
            'dragon': {'hp': 150, 'atk': 20, 'def': 10, 'exp': 100, 'gold': 100, 'loot': ['Dragon Sword', 'Dragon Stone']},
            'skeleton': {'hp': 35, 'atk': 7, 'def': 3, 'exp': 20, 'gold': 15, 'loot': ['Bone Sword', 'Health Potion']},
            'demon': {'hp': 120, 'atk': 18, 'def': 8, 'exp': 80, 'gold': 80, 'loot': ['Demon Blade', 'Dark Amulet']},
        }
        
        self.shop_items = {
            'Health Potion': {'cost': 50, 'effect': 'heal', 'amount': 30},
            'Mana Potion': {'cost': 70, 'effect': 'mana', 'amount': 50},
            'Iron Sword': {'cost': 200, 'effect': 'weapon', 'atk': 5},
            'Steel Sword': {'cost': 400, 'effect': 'weapon', 'atk': 8},
            'Dragon Sword': {'cost': 1000, 'effect': 'weapon', 'atk': 15},
            'Iron Armor': {'cost': 250, 'effect': 'armor', 'def': 5},
            'Steel Armor': {'cost': 500, 'effect': 'armor', 'def': 8},
            'Dragon Armor': {'cost': 1200, 'effect': 'armor', 'def': 15},
            'Speed Boots': {'cost': 300, 'effect': 'speed', 'bonus': 10},
            'Ancient Ring': {'cost': 600, 'effect': 'ring', 'exp_boost': 1.2},
        }
        
        self.quests = {
            1: {'name': 'Goblin Slayer', 'desc': 'Kill 5 Goblins', 'reward': 100, 'kills': 5, 'type': 'goblin'},
            2: {'name': 'Orc Hunter', 'desc': 'Kill 3 Orcs', 'reward': 200, 'kills': 3, 'type': 'orc'},
            3: {'name': 'Troll Danger', 'desc': 'Kill 2 Trolls', 'reward': 500, 'kills': 2, 'type': 'troll'},
            4: {'name': 'Dragon Slayer', 'desc': 'Kill 1 Dragon', 'reward': 1000, 'kills': 1, 'type': 'dragon'},
            5: {'name': 'Demon Lord', 'desc': 'Kill 1 Demon', 'reward': 800, 'kills': 1, 'type': 'demon'},
        }
        
        self.skills = {
            'Power Strike': {'cost': 20, 'damage_mult': 2.0, 'description': 'Double damage attack'},
            'Heavy Defense': {'cost': 15, 'defense_mult': 2.0, 'description': 'Double defense for 1 turn'},
            'Quick Strike': {'cost': 10, 'damage_mult': 1.5, 'description': '1.5x damage'},
            'Heal': {'cost': 25, 'heal_amount': 100, 'description': 'Restore 100 HP'},
        }
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"[✓] Server started on {self.host}:{self.port}")
        print("[*] Waiting for connections...\n")
        
        try:
            while True:
                client, addr = server.accept()
                print(f"[+] {addr} connected")
                thread = threading.Thread(target=self.handle_client, args=(client, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n[!] Server shutting down...")
            server.close()
    
    def handle_client(self, client, addr):
        try:
            while True:
                data = self.recv_json(client)
                if not data:
                    break
                
                print(f"[<] {addr} -> {data.get('cmd')}")
                response = self.process(data)
                
                if not self.send_json(client, response):
                    break
                    
        except Exception as e:
            print(f"[!] Error {addr}: {e}")
        finally:
            client.close()
            print(f"[-] {addr} disconnected\n")
    
    def recv_json(self, client):
        try:
            size_data = client.recv(4)
            if not size_data:
                return None
            size = int(size_data.decode())
            data = b''
            while len(data) < size:
                chunk = client.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            return json.loads(data.decode())
        except:
            return None
    
    def send_json(self, client, data):
        try:
            msg = json.dumps(data).encode()
            size = str(len(msg)).zfill(4).encode()
            client.send(size + msg)
            return True
        except:
            return False
    
    def process(self, data):
        cmd = data.get('cmd')
        
        if cmd == 'register':
            return self.register(data)
        elif cmd == 'login':
            return self.login(data)
        elif cmd == 'hunt':
            return self.hunt(data)
        elif cmd == 'pvp':
            return self.pvp(data)
        elif cmd == 'shop_list':
            return self.shop_list()
        elif cmd == 'buy_item':
            return self.buy_item(data)
        elif cmd == 'sell_item':
            return self.sell_item(data)
        elif cmd == 'quest_list':
            return self.quest_list()
        elif cmd == 'accept_quest':
            return self.accept_quest(data)
        elif cmd == 'complete_quest':
            return self.complete_quest(data)
        elif cmd == 'skill_list':
            return self.skill_list()
        elif cmd == 'use_skill':
            return self.use_skill(data)
        elif cmd == 'dungeon':
            return self.dungeon(data)
        elif cmd == 'daily_reward':
            return self.daily_reward(data)
        elif cmd == 'stats':
            return self.get_stats(data)
        elif cmd == 'inventory':
            return self.get_inventory(data)
        elif cmd == 'equip':
            return self.equip_item(data)
        elif cmd == 'rest':
            return self.rest(data)
        elif cmd == 'leaderboard':
            return self.leaderboard()
        elif cmd == 'players_online':
            return {'status': 'ok', 'count': len(self.clients), 'players': list(self.clients.keys())}
        else:
            return {'status': 'error', 'msg': 'Unknown command'}
    
    def register(self, data):
        name = data.get('name')
        char_class = data.get('class')
        
        if not name or not char_class:
            return {'status': 'error', 'msg': 'Invalid data'}
        
        if self.db.player_exists(name):
            return {'status': 'error', 'msg': 'Name already taken'}
        
        classes = {
            'Warrior': {'hp': 100, 'atk': 15, 'def': 8},
            'Mage': {'hp': 70, 'atk': 20, 'def': 5},
            'Rogue': {'hp': 85, 'atk': 18, 'def': 6},
            'Paladin': {'hp': 110, 'atk': 12, 'def': 10},
            'Archer': {'hp': 80, 'atk': 17, 'def': 6},
            'Berserker': {'hp': 120, 'atk': 22, 'def': 6},
        }
        
        if char_class not in classes:
            return {'status': 'error', 'msg': 'Invalid class'}
        
        stats = classes[char_class]
        player = {
            'name': name,
            'class': char_class,
            'level': 1,
            'exp': 0,
            'exp_max': 100,
            'hp': stats['hp'],
            'max_hp': stats['hp'],
            'mana': 100,
            'max_mana': 100,
            'atk': stats['atk'],
            'def': stats['def'],
            'speed': 10,
            'gold': 100,
            'inventory': ['Health Potion', 'Health Potion'],
            'weapon': None,
            'armor': None,
            'ring': None,
            'kills': 0,
            'deaths': 0,
            'battles': 0,
            'pvp_wins': 0,
            'pvp_loses': 0,
            'active_quests': [],
            'completed_quests': [],
            'daily_reward_time': 0,
            'dungeon_level': 0,
            'skills': ['Quick Strike'],
            'created': datetime.now().isoformat()
        }
        
        self.db.save_player(player)
        self.clients[name] = True
        
        return {'status': 'ok', 'msg': 'Character created', 'player': player}
    
    def login(self, data):
        name = data.get('name')
        if not name:
            return {'status': 'error', 'msg': 'Invalid name'}
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        self.clients[name] = True
        return {'status': 'ok', 'msg': 'Login success', 'player': player}
    
    def hunt(self, data):
        name = data.get('player')
        difficulty = data.get('difficulty', 'goblin')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if player['hp'] <= 0:
            return {'status': 'error', 'msg': 'Dead! Rest first'}
        
        if difficulty not in self.monsters:
            return {'status': 'error', 'msg': 'Invalid monster'}
        
        monster = self.monsters[difficulty].copy()
        player['battles'] += 1
        
        log = []
        p_hp = player['hp']
        m_hp = monster['hp']
        
        while p_hp > 0 and m_hp > 0:
            dmg = max(1, player['atk'] - monster['def'] + random.randint(-2, 2))
            m_hp -= dmg
            log.append(f"You deal {dmg} dmg")
            
            if m_hp > 0:
                dmg = max(1, monster['atk'] - player['def'] + random.randint(-2, 2))
                p_hp -= dmg
                log.append(f"Monster deals {dmg} dmg")
        
        if p_hp > 0:
            exp = monster['exp']
            gold = monster['gold']
            loot = random.choice(monster.get('loot', ['Gold']))
            
            player['exp'] += exp
            player['gold'] += gold
            player['inventory'].append(loot)
            player['hp'] = p_hp
            player['kills'] += 1
            
            levelup = False
            if player['exp'] >= player['exp_max']:
                player['level'] += 1
                player['exp'] = 0
                player['exp_max'] = player['level'] * 100
                player['max_hp'] += 10
                player['atk'] += 2
                player['def'] += 1
                player['hp'] = player['max_hp']
                levelup = True
            
            self.db.save_player(player)
            
            return {
                'status': 'ok',
                'result': 'victory',
                'log': log,
                'exp': exp,
                'gold': gold,
                'loot': loot,
                'levelup': levelup,
                'player': player
            }
        else:
            player['hp'] = 0
            player['deaths'] += 1
            player['gold'] = max(0, player['gold'] - 20)
            self.db.save_player(player)
            
            return {
                'status': 'ok',
                'result': 'defeat',
                'log': log,
                'player': player
            }
    
    def pvp(self, data):
        try:
            p1_name = data.get('player')
            p2_name = data.get('opponent')
            
            if not p1_name or not p2_name:
                return {'status': 'error', 'msg': 'Invalid player names'}
            
            p1 = self.db.get_player(p1_name)
            p2 = self.db.get_player(p2_name)
            
            if not p1:
                return {'status': 'error', 'msg': f'Player {p1_name} not found'}
            
            if not p2:
                return {'status': 'error', 'msg': f'Opponent {p2_name} not found'}
            
            if p1['hp'] <= 0:
                return {'status': 'error', 'msg': 'You are dead! Rest first'}
            
            if p2['hp'] <= 0:
                return {'status': 'error', 'msg': 'Opponent is dead! Find another opponent'}
            
            if p1_name == p2_name:
                return {'status': 'error', 'msg': 'Cannot PVP yourself'}
            
            log = []
            p1_hp = p1['hp']
            p2_hp = p2['hp']
            rounds = 0
            max_rounds = 50
            
            while p1_hp > 0 and p2_hp > 0 and rounds < max_rounds:
                rounds += 1
                
                # P1 attack
                dmg = max(1, p1['atk'] - p2['def'] + random.randint(-2, 2))
                p2_hp -= dmg
                log.append(f"{p1_name} deals {dmg} dmg")
                
                if p2_hp <= 0:
                    break
                
                # P2 attack
                dmg = max(1, p2['atk'] - p1['def'] + random.randint(-2, 2))
                p1_hp -= dmg
                log.append(f"{p2_name} deals {dmg} dmg")
            
            # Determine winner
            if p1_hp > 0:
                reward = 50 + (p2['level'] * 10)
                p1['pvp_wins'] += 1
                p1['gold'] += reward
                p1['hp'] = max(1, p1_hp)
                p2['pvp_loses'] += 1
                p2['hp'] = 0
                result = f"{p1_name} WIN!"
                winner = True
            else:
                reward = 50 + (p1['level'] * 10)
                p2['pvp_wins'] += 1
                p2['gold'] += reward
                p2['hp'] = max(1, p2_hp)
                p1['pvp_loses'] += 1
                p1['hp'] = 0
                result = f"{p2_name} WIN!"
                winner = False
            
            # Save both players
            self.db.save_player(p1)
            self.db.save_player(p2)
            
            return {
                'status': 'ok',
                'log': log,
                'result': result,
                'reward': reward,
                'winner': winner,
                'player': p1
            }
        except Exception as e:
            print(f"[PVP ERROR] {e}")
            return {'status': 'error', 'msg': f'PVP error: {str(e)}'}
    
    def shop_list(self):
        return {'status': 'ok', 'shop': self.shop_items}
    
    def buy_item(self, data):
        name = data.get('player')
        item = data.get('item')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if item not in self.shop_items:
            return {'status': 'error', 'msg': 'Item not found'}
        
        cost = self.shop_items[item]['cost']
        
        if player['gold'] < cost:
            return {'status': 'error', 'msg': 'Not enough gold'}
        
        player['gold'] -= cost
        player['inventory'].append(item)
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': f'Bought {item}', 'player': player}
    
    def sell_item(self, data):
        name = data.get('player')
        item = data.get('item')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if item not in player['inventory']:
            return {'status': 'error', 'msg': 'Item not in inventory'}
        
        if item not in self.shop_items:
            return {'status': 'error', 'msg': 'Cannot sell this item'}
        
        sell_price = int(self.shop_items[item]['cost'] * 0.5)
        player['gold'] += sell_price
        player['inventory'].remove(item)
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': f'Sold {item} for {sell_price} gold', 'player': player}
    
    def quest_list(self):
        return {'status': 'ok', 'quests': self.quests}
    
    def accept_quest(self, data):
        name = data.get('player')
        quest_id = data.get('quest_id')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if quest_id in player['active_quests']:
            return {'status': 'error', 'msg': 'Quest already active'}
        
        player['active_quests'].append(quest_id)
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': f'Quest {quest_id} accepted'}
    
    def complete_quest(self, data):
        name = data.get('player')
        quest_id = data.get('quest_id')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if quest_id not in player['active_quests']:
            return {'status': 'error', 'msg': 'Quest not active'}
        
        quest = self.quests.get(quest_id)
        if not quest:
            return {'status': 'error', 'msg': 'Quest not found'}
        
        player['active_quests'].remove(quest_id)
        player['completed_quests'].append(quest_id)
        player['gold'] += quest['reward']
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': 'Quest completed!', 'reward': quest['reward']}
    
    def skill_list(self):
        return {'status': 'ok', 'skills': self.skills}
    
    def use_skill(self, data):
        name = data.get('player')
        skill = data.get('skill')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if skill not in self.skills:
            return {'status': 'error', 'msg': 'Skill not found'}
        
        if player['mana'] < self.skills[skill]['cost']:
            return {'status': 'error', 'msg': 'Not enough mana'}
        
        player['mana'] -= self.skills[skill]['cost']
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': f'Used {skill}', 'player': player}
    
    def dungeon(self, data):
        name = data.get('player')
        player = self.db.get_player(name)
        
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        level = player.get('dungeon_level', 0) + 1
        difficulty = ['goblin', 'orc', 'troll', 'dragon'][min(level-1, 3)]
        
        result = self.hunt({'player': name, 'difficulty': difficulty})
        
        if result['result'] == 'victory':
            player['dungeon_level'] = level
            self.db.save_player(player)
            result['msg'] = f'Dungeon Level {level} cleared!'
        
        return result
    
    def daily_reward(self, data):
        name = data.get('player')
        player = self.db.get_player(name)
        
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        now = time.time()
        if now - player.get('daily_reward_time', 0) < 86400:
            return {'status': 'error', 'msg': 'Daily reward already claimed'}
        
        reward = random.randint(100, 500)
        player['gold'] += reward
        player['daily_reward_time'] = now
        self.db.save_player(player)
        
        return {'status': 'ok', 'msg': f'Daily reward: {reward} gold', 'reward': reward}
    
    def get_stats(self, data):
        name = data.get('player')
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        return {'status': 'ok', 'player': player}
    
    def get_inventory(self, data):
        name = data.get('player')
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        return {
            'status': 'ok',
            'inventory': player['inventory'],
            'weapon': player['weapon'],
            'armor': player['armor'],
            'ring': player['ring']
        }
    
    def equip_item(self, data):
        name = data.get('player')
        item = data.get('item')
        
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        if item not in player['inventory']:
            return {'status': 'error', 'msg': 'Item not in inventory'}
        
        if item not in self.shop_items:
            return {'status': 'error', 'msg': 'Invalid item'}
        
        item_info = self.shop_items[item]
        
        if item_info.get('effect') == 'weapon':
            if player['weapon']:
                player['inventory'].append(player['weapon'])
            player['weapon'] = item
            player['inventory'].remove(item)
            player['atk'] += item_info['atk']
        elif item_info.get('effect') == 'armor':
            if player['armor']:
                player['inventory'].append(player['armor'])
            player['armor'] = item
            player['inventory'].remove(item)
            player['def'] += item_info['def']
        elif item_info.get('effect') == 'ring':
            if player['ring']:
                player['inventory'].append(player['ring'])
            player['ring'] = item
            player['inventory'].remove(item)
        
        self.db.save_player(player)
        return {'status': 'ok', 'msg': f'Equipped {item}', 'player': player}
    
    def rest(self, data):
        name = data.get('player')
        player = self.db.get_player(name)
        if not player:
            return {'status': 'error', 'msg': 'Player not found'}
        
        player['hp'] = player['max_hp']
        player['mana'] = player['max_mana']
        self.db.save_player(player)
        return {'status': 'ok', 'msg': 'Fully restored', 'player': player}
    
    def leaderboard(self):
        players = sorted(
            self.db.players.values(),
            key=lambda x: (x['level'], x['exp']),
            reverse=True
        )[:20]
        return {'status': 'ok', 'leaderboard': players}

if __name__ == '__main__':
    try:
        server = GameServer()
        server.start()
    except KeyboardInterrupt:
        print("\n[!] Shutdown")
    except Exception as e:
        print(f"[ERROR] {e}")

