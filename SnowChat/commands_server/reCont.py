def run(client, nickname, clients, nick_to_sock, active_chats, log_chat, msg):
    try:
        target_nick = msg.split(" ", 1)[1].strip()
    except IndexError:
        client.send("[시스템] 사용법: !reCont <상대닉네임>".encode())
        return

    if target_nick in nick_to_sock:
        active_chats[nickname] = target_nick
        active_chats[target_nick] = nickname
        client.send(f"[시스템] '{target_nick}' 님과의 대화를 이어서 시작합니다.".encode())
        nick_to_sock[target_nick].send(f"[시스템] '{nickname}' 님이 다시 연결했습니다.".encode())
    else:
        client.send("[시스템] 대상 사용자가 온라인이 아닙니다.".encode())
