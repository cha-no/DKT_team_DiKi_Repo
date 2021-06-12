import os
import argparse

def parse_args(mode='train'):
    parser = argparse.ArgumentParser()

    # utils argument
    parser.add_argument('--seed', default=42, type=int, help='seed')
    # dataloader argument
    parser.add_argument('--data_dir', default='../data/', type=str, help='data directory')
    parser.add_argument('--file_name', default='train_data.csv', type=str, help='train file name')
    parser.add_argument('--asset_dir', default='asset/', type=str, help='data directory')
    parser.add_argument('--max_seq_len', default=256, type=int, help='max sequence length')
    parser.add_argument('--num_workers', default=1, type=int, help='model file name')
    parser.add_argument('--batch_size', default=64, type=int, help='batch size')

    # model argument
    parser.add_argument('--model_dir', default='models/', type=str, help='model directory')
    parser.add_argument('--model_name', default='model.pt', type=str, help='model file name')

    # train argument
    parser.add_argument('--device', default='cpu', type=str, help='cpu or gpu')
    parser.add_argument('--n_epochs', default=100, type=int, help='number of epochs')
    parser.add_argument('--lr', default=0.0001, type=float, help='learning rate')
    parser.add_argument('--clip_grad', default=10, type=int, help='clip grad')
    parser.add_argument('--patience', default=20, type=int, help='for early stopping')

    # model argument
    parser.add_argument('--model', default='lastquery', type=str, help='model type')
    parser.add_argument('--hidden_dim', default=512, type=int, help='hidden dimension size')
    parser.add_argument('--n_layers', default=3, type=int, help='number of layers')
    parser.add_argument('--n_heads', default=4, type=int, help='number of heads')
    parser.add_argument('--drop_out', default=0.3, type=int, help='drop out rate')

    # optimizer & scheduler argument
    parser.add_argument('--optimizer', default='adamW', type=str, help='optimizer type')
    parser.add_argument('--scheduler', default='plateau', type=str, help='scheduler type')

    # etc
    parser.add_argument('--log_steps', default=50, type=int, help='print log per n steps')

    # inference argument
    parser.add_argument('--output_dir', default='output/', type=str, help='output directory')
    parser.add_argument('--test_file_name', default='test_data.csv', type=str, help='test file name')

    # Tuning part : data augmentation
    parser.add_argument('--window', default=True, type=bool, help='Data augmentation')
    parser.add_argument('--stride', default=128, type=int, help='Stride size')
    parser.add_argument('--shuffle_n', default=True, type=bool, help='Shuffle On/Off')


    parser.add_argument('--kfold5', action='store_true')
    parser.add_argument('--wandb', action='store_true')
    args = parser.parse_args()
    return args