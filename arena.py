#用意されてたのがSampleClient, 追加されるのがnot_websocket_client.Client
from server.arena import Arena
if __name__ == "__main__":
    # -- Example usage --
    #
    # もし事前に定義したクライアントを渡したい場合:
    #
    from client.Back_file import SampleClient as SampleClient
    print (f"SampleClient: {SampleClient}")
    predefs = [
        [SampleClient(player_name="PreAI1", is_ai=True), "PreAI1"],
        #[SampleClient(player_name="PreAI2", is_ai=True), "PreAI2"]
    ]
    
    arena = Arena(total_matches=5, predefined_clients=predefs)
    arena.run()
    #
    
    # 事前クライアントを指定せずに起動
    
    # arena = Arena()
    # arena.run()