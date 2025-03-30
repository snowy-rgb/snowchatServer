import socket
import threading
import os
import importlib


clients = {}         # socket: nickname
nick_to_sock = {}    # nickname: socket
active_chats = {}    # nickname: 상대 nickname

def log_chat(sender, receiver, msg):
    os.makedirs("chatlog", exist_ok=True)
    path1 = f"chatlog/{sender}_{receiver}.txt"
    path2 = f"chatlog/{receiver}_{sender}.txt"
    path = path1 if os.path.exists(path1) else path2
    if not os.path.exists(path):
        path = path1
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{sender} ➝ {receiver}: {msg}\n")


def handle_client(client):
    nickname = None  # 처음엔 닉네임 없음

    while True:
        try:
            msg = client.recv(1024).decode().strip()
            
            # 1️ 먼저 닉네임 등록 처리
            if msg.startswith("!register "):
                nickname = msg.split(" ", 1)[1].strip()
                clients[client] = nickname
                nick_to_sock[nickname] = client
                print(f"[디버그] 수신된 메시지: {msg}")
                print(f"{nickname} 입장")
                continue  # 여기서 바로 다음 루프로 넘겨서 importlib로 안 넘어가게!
                
            if nickname is None:
                client.send("[시스템] 먼저 닉네임을 설정해주세요.".encode())
                continue
            
            if msg.startswith("!"):
                try:
                    command = msg.split()[0][1:]
                    cmd_module = importlib.import_module(f"commands_server.{command}")
                    cmd_module.run(client, nickname, clients, nick_to_sock, active_chats, log_chat, msg)
                except ModuleNotFoundError:
                    client.send(f"[시스템] 존재하지 않는 명령어입니다: !{command}".encode())
                except Exception as e:
                    client.send(f"[시스템] 오류 발생: {str(e)}".encode())
                continue  # 명령어 처리 끝났으면 다음 루프

            # 닉네임 등록 (가장 먼저 와야 함!)
            if msg.startswith("!register "):
                nickname = msg.split(" ", 1)[1].strip()
                clients[client] = nickname
                nick_to_sock[nickname] = client
                print(f"[디버그] 수신된 메시지: {msg}")
                print(f"{nickname} 입장")
                continue  # 여기서 바로 다음 루프로 넘어가야 함

            # 닉네임이 등록되지 않았다면 다른 작업 금지
            if nickname is None:
                client.send("[시스템] 먼저 닉네임을 설정해주세요.".encode())
                continue

            # !connect 처리
            if msg.startswith("!connect "):
                target_nick = msg.split(" ", 1)[1].strip()
                if target_nick in nick_to_sock and target_nick != nickname:
                    active_chats[nickname] = target_nick
                    active_chats[target_nick] = nickname

                    # 로그 파일 생성
                    os.makedirs("chatlog", exist_ok=True)
                    path1 = f"chatlog/{nickname}_{target_nick}.txt"
                    path2 = f"chatlog/{target_nick}_{nickname}.txt"
                    if not os.path.exists(path1) and not os.path.exists(path2):
                        with open(path1, "w", encoding="utf-8") as f:
                            f.write(f"[시스템] {nickname}와 {target_nick}의 대화 시작됨\n")

                    client.send(f"[시스템] '{target_nick}' 님과 연결되었습니다.".encode())
                    nick_to_sock[target_nick].send(f"[시스템] '{nickname}' 님이 당신과 연결했습니다.".encode())
                else:
                    client.send("[시스템] 대상 닉네임을 찾을 수 없거나 자기 자신입니다.".encode())

            # 다이렉트 채팅
            if nickname in active_chats:
                target_nick = active_chats[nickname]
                if target_nick in nick_to_sock:
                    target_sock = nick_to_sock[target_nick]
                    target_sock.send(f"[{nickname} ➝ {target_nick}]: {msg}".encode())
                    log_chat(nickname, target_nick, msg)
                else:
                    client.send("[시스템] 상대방이 나갔습니다.".encode())
                    del active_chats[nickname]

            # 다시 연결
            if msg.startswith("!reCont "):
                target_nick = msg.split(" ", 1)[1].strip()
                if target_nick in nick_to_sock:
                    active_chats[nickname] = target_nick
                    active_chats[target_nick] = nickname
                    client.send(f"[시스템] '{target_nick}' 님과의 대화를 이어서 시작합니다.".encode())
                    nick_to_sock[target_nick].send(f"[시스템] '{nickname}' 님이 다시 연결했습니다.".encode())
                else:
                    client.send("[시스템] 대상 사용자가 온라인이 아닙니다.".encode())

            # 일반 브로드캐스트
            else:
                for c in clients:
                    if c != client:
                        c.send(f"{nickname}: {msg}".encode())

        except:
            print(f"{nickname} 퇴장")
            if nickname:
                if nickname in nick_to_sock:
                    del nick_to_sock[nickname]
                if nickname in active_chats:
                    partner = active_chats[nickname]
                    if partner in active_chats:
                        del active_chats[partner]
                    del active_chats[nickname]
            if client in clients:
                del clients[client]
            client.close()
            break




# 서버 설정
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 7878))
server.listen()
print("서버 시작됨. 대기 중...")

while True:
    client, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(client,))
    thread.start()
