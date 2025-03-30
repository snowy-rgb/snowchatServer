def run(client, nickname, clients, nick_to_sock, active_chats, log_chat, msg):
    try:
        target_nick = msg.split(" ", 1)[1].strip()
    except IndexError:
        client.send("[시스템] 사용법: !connect <상대닉네임>".encode())
        return

    if target_nick in nick_to_sock and target_nick != nickname:
        active_chats[nickname] = target_nick
        active_chats[target_nick] = nickname

        path1 = f"chatlog/{nickname}_{target_nick}.txt"
        path2 = f"chatlog/{target_nick}_{nickname}.txt"
        if not os.path.exists(path1) and not os.path.exists(path2):
            with open(path1, "w", encoding="utf-8") as f:
                f.write(f"[시스템] {nickname}와 {target_nick}의 대화 시작됨\n")

        client.send(f"[시스템] '{target_nick}' 님과 연결되었습니다.".encode())
        nick_to_sock[target_nick].send(f"[시스템] '{nickname}' 님이 당신과 연결했습니다.".encode())
    else:
        client.send("[시스템] 대상 닉네임을 찾을 수 없거나 자기 자신입니다.".encode())
