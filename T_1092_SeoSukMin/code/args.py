import os
import argparse


def parse_args(mode='train'):
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--seed', default=42, type=int, help='seed')
    
    # parser.add_argument('--device', default='cpu', type=str, help='cpu or gpu')
    parser.add_argument('--device', default='gpu', type=str, help='cpu or gpu')

    parser.add_argument('--data_dir', default='/opt/ml/input/data/train_dataset', type=str, help='data directory')
    parser.add_argument('--asset_dir', default='asset/', type=str, help='data directory')
    
    # parser.add_argument('--file_name', default='train_test_data.csv', type=str, help='train file name')
    # parser.add_argument('--file_name', default='train_test_droplast_data.csv', type=str, help='train file name')
    parser.add_argument('--file_name', default='train_test_nominus.csv', type=str, help='train file name')
    parser.add_argument('--file_name_val', default='train_data_T.csv', type=str, help='train file name')
    parser.add_argument('--fold', default=0, type=int, help='validation split fold 20%')
    
    parser.add_argument('--model_dir', default='models/', type=str, help='model directory')
    # parser.add_argument('--model_name', default='lstm.pt', type=str, help='model file name')
    parser.add_argument('--model_name', default='gpt2.pt', type=str, help='model file name')
    # parser.add_argument('--model_name', default='lstm_attn.pt', type=str, help='model file name')

    parser.add_argument('--name', default='gpt2_All_Fe14_Hi64_SQ200_lossAll_cutaugRShort_V2kfold0', type=str, help='model file name')
    # parser.add_argument('--name', default='bert_seqeunce20', type=str, help='model file name')
    # parser.add_argument('--name', default='lstm_attn', type=str, help='model file name')

    parser.add_argument('--output_dir', default='output/', type=str, help='output directory')
    parser.add_argument('--test_file_name', default='test_data_T.csv', type=str, help='test file name')
    
    parser.add_argument('--max_seq_len', default=200, type=int, help='max sequence length')
    parser.add_argument('--num_workers', default=4, type=int, help='number of workers')

    # 모델
    # parser.add_argument('--hidden_dim', default=64, type=int, help='hidden dimension size')
    parser.add_argument('--n_layers', default=2, type=int, help='number of layers')
    parser.add_argument('--n_heads', default=2, type=int, help='number of heads')
    parser.add_argument('--drop_out', default=0.2, type=float, help='drop out rate')

    parser.add_argument('--hidden_dim', default=64, type=int, help='hidden dimension size')
    # parser.add_argument('--n_layers', default=4, type=int, help='number of layers')
    # parser.add_argument('--n_heads', default=4, type=int, help='number of heads')
    # parser.add_argument('--drop_out', default=0.5, type=float, help='drop out rate')
    # parser.add_argument('--drop_out', default=0.7, type=float, help='drop out rate')
    
    # 훈련
    parser.add_argument('--n_epochs', default=400, type=int, help='number of epochs')
    parser.add_argument('--batch_size', default=64, type=int, help='batch size')
    # parser.add_argument('--batch_size', default=1024, type=int, help='batch size')
    parser.add_argument('--lr', default=1e-4, type=float, help='learning rate')
    # parser.add_argument('--lr', default=1e-5, type=float, help='learning rate')
    # parser.add_argument('--lr', default=1e-8, type=float, help='learning rate')
    parser.add_argument('--clip_grad', default=10, type=int, help='clip grad')
    parser.add_argument('--patience', default=50, type=int, help='for early stopping')
    

    parser.add_argument('--log_steps', default=50, type=int, help='print log per n steps')
    

    ### 중요 ###
    # parser.add_argument('--model', default='lstm', type=str, help='model type')
    parser.add_argument('--model', default='gpt2', type=str, help='model type')
    # parser.add_argument('--model', default='lstmattn', type=str, help='model type')
    # parser.add_argument('--optimizer', default='adam', type=str, help='optimizer type')
    parser.add_argument('--optimizer', default='adamW', type=str, help='optimizer type')
    parser.add_argument('--scheduler', default='plateau', type=str, help='scheduler type')
    # parser.add_argument('--scheduler', default='multisteplr', type=str, help='scheduler type')
    # parser.add_argument('--scheduler', default='cosine_annealing_warmup_restarts', type=str, help='scheduler type')
    
    args = parser.parse_args()

    return args