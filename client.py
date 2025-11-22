#!/usr/bin/env python3
"""
RPG Game Client - FULL FEATURED
Dengan: PVP, Shop, Guild, Quest, Skill, Dungeon, Daily Rewards
Simpan sebagai: client.py
Jalankan: python client.py
"""

import socket
import json
import os
import time
import sys

class RPGClient:
    def __init__(self):
        self.socket = None
        self.online = False
        self.player = None
        
        self.classes = {
            '1': 'Warrior',
            '2': 'Mage',
            '3': 'Rogue',
            '4': 'Paladin',
            '5': 'Archer',
            '6': 'Berserker'
        }
        
        self.class_stats = {
            'Warrior': {'hp': 100, 'atk': 15, 'def': 8},
            'Mage': {'hp': 70, 'atk': 20, 'def': 5},
            'Rogue': {'hp': 85, 'atk': 18, 'def': 6},
            'Paladin': {'hp': 110, 'atk': 12, 'def': 10},
            'Archer': {'hp': 80, 'atk': 17, 'def': 6},
            'Berserker': {'hp': 120, 'atk': 22, 'def': 6},
        }
        
        self.monsters = {
            '1': 'goblin',
            '2': 'orc',
            '3': 'troll',
            '4': 'dragon',
            '5': 'skeleton',
            '6': 'demon'
        }
    
    def clear(self):
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def header(self, text):
        print("\n" + "="*60)
        print(f"  {text:^56}")
        print("="*60 + "\n")
    
    def connect(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, int(port)))
            self.online = True
            print(f"[✓] Connected to {host}:{port}")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"[✗] {e}")
            self.online = False
            return False
    
    def send(self, data):
        if not self.online:
            return {'status': 'error', 'msg': 'Not connected'}
        
        try:
            msg = json.dumps(data).encode()
            size = str(len(msg)).zfill(4).encode()
            self.socket.send(size + msg)
            
            size_data = self.socket.recv(4)
            if not size_data:
                return {'status': 'error', 'msg': 'Connection lost'}
            
            size = int(size_data.decode())
            resp = b''
            while len(resp) < size:
                chunk = self.socket.recv(size - len(resp))
                if not chunk:
                    return {'status': 'error', 'msg': 'Connection lost'}
                resp += chunk
            
            return json.loads(resp.decode())
        except Exception as e:
            print(f"[ERROR] {e}")
            self.online = False
            return {'status': 'error', 'msg': str(e)}
    
    def main(self):
        while True:
            self.clear()
            self.header("🎮 EPIC RPG GAME 🎮")
            print("1. Play Online")
            print("2. Play Offline")
            print("3. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                self.online_mode()
            elif choice == '2':
                self.offline_mode()
            elif choice == '3':
                print("\nGoodbye!\n")
                break
    
    def online_mode(self):
        self.clear()
        self.header("ONLINE MODE")
        
        host = input("Host (default: localhost): ").strip() or 'localhost'
        port = input("Port (default: 5555): ").strip() or '5555'
        
        if self.connect(host, port):
            self.character_select()
    
    def offline_mode(self):
        self.clear()
        self.header("OFFLINE MODE")
        print("Note: Progress will NOT be saved\n")
        self.online = False
        input("Press Enter...")
        self.character_select()
    
    def character_select(self):
        while True:
            self.clear()
            self.header("CHARACTER")
            print("1. Create New")
            print("2. Login")
            print("3. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                self.create_char()
            elif choice == '2' and self.online:
                self.login_char()
            elif choice == '3':
                return
    
    def create_char(self):
        self.clear()
        self.header("CREATE CHARACTER")
        
        name = input("Name: ").strip()
        if not name:
            print("Invalid name!")
            time.sleep(2)
            return
        
        print("\nClass:")
        print("1. Warrior  (HP:100 ATK:15 DEF:8)")
        print("2. Mage     (HP:70  ATK:20 DEF:5)")
        print("3. Rogue    (HP:85  ATK:18 DEF:6)")
        print("4. Paladin  (HP:110 ATK:12 DEF:10)")
        print("5. Archer   (HP:80  ATK:17 DEF:6)")
        print("6. Berserker(HP:120 ATK:22 DEF:6)")
        
        cls_choice = input("\nClass: ").strip()
        if cls_choice not in self.classes:
            print("Invalid!")
            time.sleep(2)
            return
        
        char_class = self.classes[cls_choice]
        
        if self.online:
            print("\n[*] Creating...")
            resp = self.send({
                'cmd': 'register',
                'name': name,
                'class': char_class
            })
            
            if resp.get('status') == 'ok':
                self.player = resp['player']
                print(f"[✓] Created!")
                time.sleep(2)
                self.game_loop()
            else:
                print(f"[✗] {resp.get('msg')}")
                time.sleep(2)
        else:
            stats = self.class_stats[char_class]
            self.player = {
                'name': name,
                'class': char_class,
                'level': 1,
                'exp': 0,
                'exp_max': 100,
                'hp': stats['hp'],
                'max_hp': stats['hp'],
                'atk': stats['atk'],
                'def': stats['def'],
                'gold': 100,
                'inventory': ['Health Potion', 'Health Potion'],
                'weapon': None,
                'armor': None,
                'kills': 0,
                'pvp_wins': 0,
            }
            print(f"[✓] Created (Offline)")
            time.sleep(2)
            self.game_loop()
    
    def login_char(self):
        self.clear()
        self.header("LOGIN")
        
        name = input("Name: ").strip()
        
        print("[*] Loading...")
        resp = self.send({'cmd': 'login', 'name': name})
        
        if resp.get('status') == 'ok':
            self.player = resp['player']
            print("[✓] Logged in!")
            time.sleep(2)
            self.game_loop()
        else:
            print(f"[✗] {resp.get('msg')}")
            time.sleep(2)
    
    def game_loop(self):
        while True:
            self.clear()
            self.header("GAME MENU")
            
            p = self.player
            mode = "ONLINE" if self.online else "OFFLINE"
            print(f"{p['name']:20} | {p['class']:12} | Lvl {p['level']}")
            print(f"HP: {p['hp']}/{p['max_hp']} | ATK: {p['atk']} | DEF: {p['def']} | Gold: {p['gold']}")
            print(f"EXP: {p['exp']}/{p['exp_max']} | {mode}\n")
            
            print("--- ADVENTURE ---")
            print("1. Hunt Monster       2. PVP Battle         3. Dungeon")
            print("\n--- SHOP & ITEMS ---")
            print("4. Shop               5. Inventory          6. Equip Item")
            print("\n--- SYSTEM ---")
            print("7. Quest              8. Skills             9. Daily Reward")
            print("10. Rest              11. Stats             12. Leaderboard")
            print("\n0. Logout")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                self.hunt()
            elif choice == '2' and self.online:
                self.pvp()
            elif choice == '3' and self.online:
                self.dungeon()
            elif choice == '4' and self.online:
                self.shop()
            elif choice == '5':
                self.inventory()
            elif choice == '6' and self.online:
                self.equip()
            elif choice == '7' and self.online:
                self.quest()
            elif choice == '8' and self.online:
                self.skills()
            elif choice == '9' and self.online:
                self.daily_reward()
            elif choice == '10':
                self.rest()
            elif choice == '11' and self.online:
                self.stats()
            elif choice == '12' and self.online:
                self.leaderboard()
            elif choice == '0':
                break
    
    def hunt(self):
        self.clear()
        self.header("HUNT MONSTER")
        
        print("1. Goblin (Easy)      4. Dragon (Very Hard)")
        print("2. Orc (Normal)       5. Skeleton (Easy)")
        print("3. Troll (Hard)       6. Demon (Hard)")
        print("0. Back")
        
        choice = input("\nChoice: ").strip()
        
        if choice not in self.monsters:
            return
        
        difficulty = self.monsters[choice]
        
        if self.online:
            print("\n[*] Fighting...")
            resp = self.send({
                'cmd': 'hunt',
                'player': self.player['name'],
                'difficulty': difficulty
            })
            
            if resp.get('status') != 'ok':
                print(f"[✗] {resp.get('msg')}")
                time.sleep(2)
                return
            
            print("\nBattle Log:")
            for line in resp['log']:
                print(f"  {line}")
                time.sleep(0.2)
            
            result = resp.get('result')
            if result == 'victory':
                print(f"\n[✓ VICTORY!]")
                print(f"  EXP: +{resp['exp']}")
                print(f"  Gold: +{resp['gold']}")
                print(f"  Loot: {resp['loot']}")
                if resp['levelup']:
                    print(f"  [⭐ LEVEL UP to {resp['player']['level']}!]")
            else:
                print(f"\n[✗ DEFEAT!]")
            
            self.player = resp['player']
        else:
            print("Online only!")
        
        input("\nPress Enter...")
    
    def pvp(self):
        self.clear()
        self.header("PVP BATTLE")
        
        print("Enter opponent name to challenge:\n")
        opponent = input("Opponent: ").strip()
        
        if not opponent:
            print("[✗] Invalid name!")
            time.sleep(2)
            return
        
        if opponent == self.player['name']:
            print("[✗] Cannot PVP yourself!")
            time.sleep(2)
            return
        
        print("\n[*] Searching for opponent...")
        time.sleep(1)
        
        try:
            resp = self.send({
                'cmd': 'pvp',
                'player': self.player['name'],
                'opponent': opponent
            })
            
            if resp.get('status') != 'ok':
                print(f"[✗] {resp.get('msg')}")
                time.sleep(2)
                return
            
            print("\n⚔️ BATTLE START! ⚔️\n")
            
            for line in resp.get('log', []):
                print(f"  {line}")
                time.sleep(0.15)
            
            result = resp.get('result', '')
            reward = resp.get('reward', 0)
            
            print(f"\n{result}")
            print(f"💰 Reward: +{reward} gold")
            
            if resp.get('player'):
                self.player = resp['player']
            
        except Exception as e:
            print(f"[✗] {e}")
        
        input("\nPress Enter...")
    
    def dungeon(self):
        self.clear()
        self.header("DUNGEON EXPEDITION")
        
        print("[*] Entering dungeon...")
        resp = self.send({
            'cmd': 'dungeon',
            'player': self.player['name']
        })
        
        if resp.get('status') != 'ok':
            print(f"[✗] {resp.get('msg')}")
            time.sleep(2)
            return
        
        print("\nBattle Log:")
        for line in resp['log']:
            print(f"  {line}")
            time.sleep(0.2)
        
        result = resp.get('result')
        if result == 'victory':
            print(f"\n[✓ CLEARED!]")
            print(f"  {resp.get('msg')}")
        else:
            print(f"\n[✗ FAILED!]")
        
        self.player = resp['player']
        input("\nPress Enter...")
    
    def shop(self):
        self.clear()
        self.header("SHOP")
        
        resp = self.send({'cmd': 'shop_list'})
        
        if resp.get('status') == 'ok':
            shop = resp['shop']
            print(f"Your Gold: {self.player['gold']}\n")
            
            for i, (name, info) in enumerate(shop.items(), 1):
                print(f"{i}. {name:20} | {info['cost']:4} gold | {info.get('effect', 'misc')}")
            
            print("\n1. Buy Item")
            print("2. Sell Item")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                item = input("Item name: ").strip()
                resp = self.send({
                    'cmd': 'buy_item',
                    'player': self.player['name'],
                    'item': item
                })
                print(f"\n{resp['msg']}")
                if resp.get('status') == 'ok':
                    self.player = resp['player']
                time.sleep(2)
            elif choice == '2':
                item = input("Item name: ").strip()
                resp = self.send({
                    'cmd': 'sell_item',
                    'player': self.player['name'],
                    'item': item
                })
                print(f"\n{resp['msg']}")
                if resp.get('status') == 'ok':
                    self.player = resp['player']
                time.sleep(2)
    
    def inventory(self):
        self.clear()
        self.header("INVENTORY")
        
        if self.online:
            resp = self.send({'cmd': 'inventory', 'player': self.player['name']})
            if resp.get('status') != 'ok':
                print(f"[✗] {resp.get('msg')}")
                input("\nPress Enter...")
                return
            
            print("Items:")
            for item in resp['inventory']:
                print(f"  - {item}")
            
            print(f"\nEquipped:")
            print(f"  Weapon: {resp['weapon'] or 'None'}")
            print(f"  Armor: {resp['armor'] or 'None'}")
        else:
            print("Inventory:")
            for item in self.player['inventory']:
                print(f"  - {item}")
        
        input("\nPress Enter...")
    
    def equip(self):
        self.clear()
        self.header("EQUIP ITEM")
        
        resp = self.send({'cmd': 'inventory', 'player': self.player['name']})
        
        print("Items in inventory:")
        for item in resp['inventory']:
            print(f"  - {item}")
        
        item = input("\nItem to equip: ").strip()
        
        resp = self.send({
            'cmd': 'equip',
            'player': self.player['name'],
            'item': item
        })
        
        print(f"\n{resp['msg']}")
        if resp.get('status') == 'ok':
            self.player = resp['player']
        
        time.sleep(2)
    
    def quest(self):
        self.clear()
        self.header("QUESTS")
        
        resp = self.send({'cmd': 'quest_list'})
        
        if resp.get('status') == 'ok':
            quests = resp['quests']
            for qid, q in quests.items():
                print(f"ID: {qid} | {q['name']:20} | Reward: {q['reward']:4} gold")
            
            print("\n1. Accept Quest")
            print("2. Complete Quest")
            print("0. Back")
            
            choice = input("\nChoice: ").strip()
            
            if choice == '1':
                qid = int(input("Quest ID: ").strip())
                resp = self.send({
                    'cmd': 'accept_quest',
                    'player': self.player['name'],
                    'quest_id': qid
                })
                print(f"\n{resp['msg']}")
                time.sleep(2)
            elif choice == '2':
                qid = int(input("Quest ID: ").strip())
                resp = self.send({
                    'cmd': 'complete_quest',
                    'player': self.player['name'],
                    'quest_id': qid
                })
                print(f"\n{resp['msg']}")
                if resp.get('status') == 'ok':
                    print(f"Reward: {resp['reward']} gold")
                time.sleep(2)
    
    def skills(self):
        self.clear()
        self.header("SKILLS")
        
        resp = self.send({'cmd': 'skill_list'})
        
        if resp.get('status') == 'ok':
            skills = resp['skills']
            for i, (name, info) in enumerate(skills.items(), 1):
                print(f"{i}. {name:20} | Cost: {info['cost']:2} Mana")
                print(f"   {info['description']}")
            
            skill = input("\nSkill name: ").strip()
            resp = self.send({
                'cmd': 'use_skill',
                'player': self.player['name'],
                'skill': skill
            })
            print(f"\n{resp['msg']}")
            if resp.get('status') == 'ok':
                self.player = resp['player']
            time.sleep(2)
    
    def daily_reward(self):
        self.clear()
        self.header("DAILY REWARD")
        
        print("[*] Claiming daily reward...")
        resp = self.send({
            'cmd': 'daily_reward',
            'player': self.player['name']
        })
        
        if resp.get('status') == 'ok':
            print(f"\n[✓] {resp['msg']}")
            self.player = resp['player']
        else:
            print(f"\n[✗] {resp['msg']}")
        
        time.sleep(2)
    
    def rest(self):
        if self.online:
            resp = self.send({'cmd': 'rest', 'player': self.player['name']})
            if resp.get('status') == 'ok':
                self.player = resp['player']
                print("\n[✓] Fully restored!")
        else:
            self.player['hp'] = self.player['max_hp']
            print("\n[✓] HP restored!")
        
        time.sleep(2)
    
    def stats(self):
        self.clear()
        self.header("STATS")
        
        resp = self.send({'cmd': 'stats', 'player': self.player['name']})
        if resp.get('status') == 'ok':
            p = resp['player']
            print(f"Name: {p['name']}")
            print(f"Class: {p['class']}")
            print(f"Level: {p['level']}")
            print(f"Exp: {p['exp']}/{p['exp_max']}")
            print(f"\nCombat Stats:")
            print(f"  Kills: {p['kills']}")
            print(f"  Deaths: {p['deaths']}")
            print(f"  Battles: {p['battles']}")
            print(f"  PVP Wins: {p['pvp_wins']}")
            print(f"  PVP Loses: {p['pvp_loses']}")
            print(f"\nProgress:")
            print(f"  Dungeon Level: {p.get('dungeon_level', 0)}")
            print(f"  Quests Completed: {len(p.get('completed_quests', []))}")
        
        input("\nPress Enter...")
    
    def leaderboard(self):
        self.clear()
        self.header("TOP 20 LEADERBOARD")
        
        resp = self.send({'cmd': 'leaderboard'})
        if resp.get('status') == 'ok':
            print(f"{'Rank':<5} {'Name':<20} {'Level':<8} {'Class':<12} {'PVP':<8}")
            print("-" * 60)
            for rank, player in enumerate(resp['leaderboard'], 1):
                print(f"{rank:<5} {player['name']:<20} {player['level']:<8} {player['class']:<12} {player['pvp_wins']:<8}")
        
        input("\nPress Enter...")

if __name__ == '__main__':
    try:
        client = RPGClient()
        client.main()
    except KeyboardInterrupt:
        print("\n[!] Exit\n")
    except Exception as e:
        print(f"\n[ERROR] {e}\n")

