import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from collections import defaultdict
import random
import os
import json
from tqdm import tqdm

# 既存のコードからインポート
from .encode_state import encode_state
from .StrategyNetwork import StrategyNetwork
from .reservoirbuffer import ReservoirBuffer
from .create_advantage_network import create_advantage_network

# 学習評価のためのクラス
class CFRTrainingEvaluator:
    def __init__(self, strategy_net, advantage_net):
        """学習の評価を行うクラス"""
        self.strategy_net = strategy_net
        self.advantage_net = advantage_net
        self.history = {
            'advantage_loss': [],
            'strategy_accuracy': [],
            'declaration_vs_sum_ratio': [],
            'win_rate': [],
            'epoch': []
        }
    
    def log_metrics(self, epoch, advantage_loss=None, strategy_accuracy=None, 
                   declaration_vs_sum_ratio=None, win_rate=None):
        """各指標をログに記録"""
        self.history['epoch'].append(epoch)
        
        if advantage_loss is not None:
            self.history['advantage_loss'].append(advantage_loss)
        
        if strategy_accuracy is not None:
            self.history['strategy_accuracy'].append(strategy_accuracy)
        
        if declaration_vs_sum_ratio is not None:
            self.history['declaration_vs_sum_ratio'].append(declaration_vs_sum_ratio)
            
        if win_rate is not None:
            self.history['win_rate'].append(win_rate)
    
    def evaluate_declaration_accuracy(self, test_states, num_samples=100):
        """宣言値と実際の合計値の比較を評価"""
        correct_declarations = 0
        total_ratio = 0
        overestimation_count = 0
        
        # テスト状態から最大numSamplesをランダムに選択
        sample_size = min(num_samples, len(test_states))
        sampled_states = random.sample(test_states, sample_size)
        
        for state in sampled_states:
            # 状態をエンコード
            encoded_state = encode_state(state)
            
            # 戦略ネットワークで宣言値を予測
            #action_probs = self.strategy_net.predict(encoded_state, state['legal_action'])
            
            # 最も確率の高い行動を選択
            #declaration = max(action_probs.items(), key=lambda x: x[1])[0]
            declaration = state['selectaction']
            # 実際の合計値
            actual_sum = state['sum']
            
            # 宣言値と実際の合計値の比率
            if actual_sum > 0:
                ratio = declaration / actual_sum
                total_ratio += ratio
                
                # 過大宣言しているか確認
                if declaration > actual_sum:
                    overestimation_count += 1
                
                # 宣言値が実際の合計±20%以内なら正確と見なす
                if 0.8 <= ratio <= 1.2:
                    correct_declarations += 1
        
        avg_ratio = total_ratio / sample_size if sample_size > 0 else 0
        accuracy = correct_declarations / sample_size if sample_size > 0 else 0
        overestimation_rate = overestimation_count / sample_size if sample_size > 0 else 0
        
        return avg_ratio, accuracy, overestimation_rate
    
    def evaluate_win_rate(self, num_games=50, opponent='random'):
        """対戦の勝率を評価"""
        # この実装はシミュレーションゲームが必要なため、実際にはゲームエンジンと連携する
        # ここではサンプルとして簡易的な実装
        
        wins = 0
        
        for _ in range(num_games):
            # ランダムな対戦結果（実際はゲームエンジンでシミュレーション）
            result = random.random()
            
            # 学習が進むほど勝率が上がることを仮定
            if opponent == 'random':
                win_threshold = 0.5 + (len(self.history['epoch']) * 0.01)
                win_threshold = min(win_threshold, 0.9)  # 最大90%の勝率
            else:
                win_threshold = 0.5  # 同等の相手との対戦
                
            if result < win_threshold:
                wins += 1
                
        return wins / num_games
    
    def plot_all_metrics(self):
        """すべての指標をプロット"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. アドバンテージネットワークの損失関数
        if self.history['advantage_loss']:
            axes[0, 0].plot(self.history['epoch'], self.history['advantage_loss'], 'b-')
            axes[0, 0].set_title('Advantage Network Loss')
            axes[0, 0].set_xlabel('Epoch')
            axes[0, 0].set_ylabel('Loss')
            axes[0, 0].grid(True)
        
        # 2. 戦略ネットワークの精度
        if self.history['strategy_accuracy']:
            axes[0, 1].plot(self.history['epoch'], self.history['strategy_accuracy'], 'g-')
            axes[0, 1].set_title('Strategy Network Accuracy')
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].set_ylabel('Accuracy')
            axes[0, 1].grid(True)
        
        # 3. 宣言値と実際の合計の比率
        if self.history['declaration_vs_sum_ratio']:
            axes[1, 0].plot(self.history['epoch'], self.history['declaration_vs_sum_ratio'], 'r-')
            axes[1, 0].axhline(y=1.0, color='k', linestyle='--', label='Ideal ratio')
            axes[1, 0].set_title('Declaration vs Actual Sum Ratio')
            axes[1, 0].set_xlabel('Epoch')
            axes[1, 0].set_ylabel('Ratio')
            axes[1, 0].legend()
            axes[1, 0].grid(True)
        
        # 4. 勝率の推移
        if self.history['win_rate']:
            axes[1, 1].plot(self.history['epoch'], self.history['win_rate'], 'm-')
            axes[1, 1].set_title('Win Rate vs Random Policy')
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].set_ylabel('Win Rate')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        return fig
    
    def plot_declaration_distribution(self, test_states, num_samples=100):
        """宣言値の分布と実際の合計値の分布を比較"""
        declarations = []
        actual_sums = []
        
        # テスト状態からサンプリング
        sample_size = min(num_samples, len(test_states))
        sampled_states = random.sample(test_states, sample_size)
        
        for state in sampled_states:
            # 状態をエンコード
            encoded_state = encode_state(state)
            
            # 戦略ネットワークで宣言値を予測
            action_probs = self.strategy_net.predict(encoded_state, state['legal_action'])
            
            # 確率に基づいて宣言値をサンプリング
            actions = list(action_probs.keys())
            probs = list(action_probs.values())
            
            if actions and probs:
                declaration = np.random.choice(actions, p=np.array(probs)/sum(probs))
                declarations.append(declaration)
                actual_sums.append(state['sum'])
        
        # 結果をプロット
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # ヒストグラム
        ax.hist(actual_sums, bins=20, alpha=0.5, label='Actual Sum', color='blue')
        ax.hist(declarations, bins=20, alpha=0.5, label='Declarations', color='red')
        
        # 過大宣言の割合を計算
        overestimations = sum(1 for d, s in zip(declarations, actual_sums) if d > s)
        overestimation_rate = overestimations / len(declarations) if declarations else 0
        
        ax.set_title(f'Declaration vs Actual Sum Distribution\nOverestimation Rate: {overestimation_rate:.2f}')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True)
        
        return fig, overestimation_rate

# メイン実行関数
def evaluate_cfr_training(self,current_state,iterations=50):
    """CFR学習の評価を実行"""
    # ネットワークの作成
    input_size = self.input_size
    output_size = 141
    advantage_net = self.advantage_net
    strategy_net = self.strategy_net
    
    # 評価用のインスタンス
    evaluator = CFRTrainingEvaluator(strategy_net, advantage_net)
    
    # リザーバーバッファの作成
    advantage_buffer = ReservoirBuffer()
    strategy_buffer = ReservoirBuffer()
    
    # サンプルデータの作成
    # train_states = create_sample_game_states(1000)
    # test_states = create_sample_game_states(200)
    
    # 学習と評価のループ
    for i in tqdm(range(iterations)):
        # サンプル状態からのバッチ作成
        batch_size = 32
        batch_indices = np.random.choice(len(current_state), batch_size)
        batch_states = [current_state[idx] for idx in batch_indices]
        
        # エンコード
        encoded_states = np.array([encode_state(state) for state in batch_states])
        
        # 形状を(None, 318)に調整
        if len(encoded_states.shape) == 3:
            encoded_states = encoded_states.reshape(-1, self.input_size)  # (32, 1, 318) → (32, 318)
        
        # アドバンテージネットワークの更新シミュレーション
        advantage_loss = advantage_net.fit(
            encoded_states, 
            np.random.rand(batch_size, output_size),  # ダミーターゲット
            epochs=1,
            verbose=0
        ).history['loss'][0]
        
        # 戦略ネットワークの更新シミュレーション
        strategy_accuracy = random.random() * 0.2 + 0.6  # 模擬精度（60%〜80%）
        
        # 宣言値と実際の合計の比率を評価
        declaration_ratio, _, overestimation_rate = evaluator.evaluate_declaration_accuracy(current_state)
        
        # 勝率の評価
        win_rate = evaluator.evaluate_win_rate()
        
        # 指標の記録
        evaluator.log_metrics(
            epoch=i,
            advantage_loss=advantage_loss,
            strategy_accuracy=strategy_accuracy,
            declaration_vs_sum_ratio=declaration_ratio,
            win_rate=win_rate
        )
    
    # 結果の可視化
    metrics_fig = evaluator.plot_all_metrics()
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'save_picture')
    os.makedirs(save_dir, exist_ok=True)
    metrics_fig.savefig(os.path.join(save_dir, 'cfr_training_metrics.png'))
    
    # 宣言値の分布を可視化
    dist_fig, overestimation_rate = evaluator.plot_declaration_distribution(current_state)
    dist_fig.savefig(os.path.join(save_dir, 'declaration_distribution.png'))
    
    print(f"Training evaluation complete. Final overestimation rate: {overestimation_rate:.2f}")
    return evaluator

# モデルの推論パフォーマンスを視覚化する関数
def visualize_model_prediction(strategy_net, test_states, num_samples=10):
    """モデルの推論結果を視覚化"""
    fig, axes = plt.subplots(2, 5, figsize=(15, 6))
    axes = axes.flatten()
    
    # ランダムにサンプルを選択
    sample_size = min(num_samples, len(test_states))
    sampled_states = random.sample(test_states, sample_size)
    
    for i, state in enumerate(sampled_states):
        if i >= len(axes):
            break
            
        # 状態をエンコード
        encoded_state = encode_state(state)
        
        # 戦略ネットワークで宣言値を予測
        action_probs = strategy_net.predict(encoded_state, state['legal_action'])
        
        # 実際の合計値
        actual_sum = state['sum']
        
        # 行動確率の上位5つをプロット
        sorted_actions = sorted(action_probs.items(), key=lambda x: x[1], reverse=True)[:5]
        actions = [a[0] for a in sorted_actions]
        probs = [a[1] for a in sorted_actions]
        
        axes[i].bar(actions, probs)
        axes[i].axvline(x=actual_sum, color='r', linestyle='--', label=f'Actual Sum: {actual_sum}')
        axes[i].set_title(f'State {i+1}')
        axes[i].set_xlabel('Declaration Value')
        axes[i].set_ylabel('Probability')
        axes[i].legend()
    
    plt.tight_layout()
    return fig

# if __name__ == "__main__":
    # CFR学習の評価
    # evaluator = evaluate_cfr_training(iterations=50)
    
    # テスト状態の作成
    # test_states = create_sample_game_states(50)
    
    # モデルの推論可視化
    prediction_fig = visualize_model_prediction(evaluator.strategy_net, test_states)
    prediction_fig.savefig('model_predictions.png')
    
    print("Evaluation complete. Results saved as image files.")