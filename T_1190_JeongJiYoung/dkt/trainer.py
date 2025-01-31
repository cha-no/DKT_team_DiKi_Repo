import os
import torch
import numpy as np

from .dataloader import get_loaders, get_loader
from .augmentation import data_augmentation
from .optimizer import get_optimizer
from .scheduler import get_scheduler
from .criterion import get_criterion
from .metric import get_metric
from .model import LSTM, LSTMATTN, Bert

import wandb

def run(args, train_data, valid_data, kfold=''):

    # augmentation
    # augmented_train_data = data_augmentation(train_data, args)
    # if len(augmented_train_data) != len(train_data):
    #     print(f"Data Augmentation applied. Train data {len(train_data)} -> {len(augmented_train_data)}\n")

    train_loader, _ = get_loaders(args, train_data, None)
    
    # only when using warmup scheduler
    args.total_steps = int(len(train_loader.dataset) / args.batch_size) * (args.n_epochs)
    args.warmup_steps = args.total_steps // 10
            
    model = get_model(args)
    optimizer = get_optimizer(model, args)
    scheduler = get_scheduler(optimizer, args)

    best_auc = -1
    with_acc = -1
    early_stopping_counter = 0
    for epoch in range(args.n_epochs):

        print(f"Start Training: Epoch {epoch + 1} Fold {kfold}")
        
        ### TRAIN
        train_auc, train_acc, train_loss = train(train_loader, model, optimizer, args)
        
        ### VALID
        auc = 0.
        acc = 0.
        for i in range(5):
            if i == 0:
                valid_loader = get_loader(args, valid_data, False, False)
            else:
                np.random.seed(seed=i*10)
                valid_loader = get_loader(args, valid_data, False, True)

            v_auc, v_acc, _, _ = validate(valid_loader, model, args)
            auc += v_auc
            acc += v_acc
        auc /= 5
        acc /= 5
        np.random.seed(seed=args.seed)

        ### TODO: model save or early stopping
        if args.wandb:
            display_epoch = epoch + 1
            if kfold:
                display_epoch += (int(kfold)-1) * args.n_epochs
            wandb.log({"epoch": display_epoch, "train_loss": train_loss, "train_auc": train_auc, "train_acc":train_acc,
                    "valid_auc":auc, "valid_acc":acc, "lr":get_lr(optimizer)})
        if auc > best_auc:
            best_auc = auc
            with_acc = acc
            # torch.nn.DataParallel로 감싸진 경우 원래의 model을 가져옵니다.
            model_to_save = model.module if hasattr(model, 'module') else model
            save_checkpoint({
                'epoch': epoch + 1,
                'state_dict': model_to_save.state_dict(),
                },
                args.model_dir, f'model{kfold}.pt',
            )
            early_stopping_counter = 0
        else:
            early_stopping_counter += 1
            if early_stopping_counter >= args.patience:
                print(f'EarlyStopping counter: {early_stopping_counter} out of {args.patience}')
                break

        # scheduler
        if args.scheduler == 'plateau':
            scheduler.step(best_auc)
        else:
            scheduler.step()
    
    if args.wandb:
        wandb.log({"best_auc":best_auc, "with_acc":with_acc})
    



def train(train_loader, model, optimizer, args):
    model.train()

    total_preds = []
    total_targets = []
    losses = []
    for step, batch in enumerate(train_loader):
        input = process_batch(batch, args)
        preds = model(input)
        targets = input[-4] # correct

        
        loss = compute_loss(preds, targets)
        update_params(loss, model, optimizer, args)

        if step % args.log_steps == 0:
            print(f"Training steps: {step} Loss: {str(loss.item())}")
        
        # predictions
        preds = preds[:,-1]
        targets = targets[:,-1]

        if args.device == 'cuda':
            preds = preds.to('cpu').detach().numpy()
            targets = targets.to('cpu').detach().numpy()
        else: # cpu
            preds = preds.detach().numpy()
            targets = targets.detach().numpy()
        
        total_preds.append(preds)
        total_targets.append(targets)
        losses.append(loss)
      

    total_preds = np.concatenate(total_preds)
    total_targets = np.concatenate(total_targets)

    # Train AUC / ACC
    auc, acc = get_metric(total_targets, total_preds)
    loss_avg = sum(losses)/len(losses)
    print(f'TRAIN AUC : {auc} ACC : {acc}')
    return auc, acc, loss_avg
    

def validate(valid_loader, model, args):
    model.eval()

    total_preds = []
    total_targets = []
    for step, batch in enumerate(valid_loader):
        input = process_batch(batch, args)

        preds = model(input)
        targets = input[-4] # correct


        # predictions
        preds = preds[:,-1]
        targets = targets[:,-1]
    
        if args.device == 'cuda':
            preds = preds.to('cpu').detach().numpy()
            targets = targets.to('cpu').detach().numpy()
        else: # cpu
            preds = preds.detach().numpy()
            targets = targets.detach().numpy()

        total_preds.append(preds)
        total_targets.append(targets)

    total_preds = np.concatenate(total_preds)
    total_targets = np.concatenate(total_targets)

    # Train AUC / ACC
    auc, acc = get_metric(total_targets, total_preds)
    
    print(f'VALID AUC : {auc} ACC : {acc}')

    return auc, acc, total_preds, total_targets



def inference(args, test_data):
    kfold = 5 if args.kfold5 else 1
    kfold_total = None

    for k in range(1, kfold+1):
        if args.kfold5: args.model_name = f"model{k}.pt"
        model = load_model(args)
        model.eval()

        total_preds = np.zeros((len(test_data)))
        # TTA를 위한 반복
        for i in range(5):
            if i == 0:
                test_loader = get_loader(args, test_data, is_change=False, is_reduce=False)
            else:
                np.random.seed(i*10)
                test_loader = get_loader(args, test_data, is_change=False, is_reduce=True)
            
            all_preds = []
            for step, batch in enumerate(test_loader):
                input = process_batch(batch, args)
                preds = model(input)
                # predictions
                preds = preds[:, -1]

                if args.device == 'cuda':
                    preds = preds.to('cpu').detach().numpy()
                else: # cpu
                    preds = preds.detach().numpy()
                
                all_preds += list(preds)

            total_preds += all_preds

        # END Prediction
        np.random.seed(args.seed)
        total_preds /= 5

        if kfold_total is None:
            kfold_total = total_preds
        else:
            kfold_total += total_preds

    # kfold 라면 평균
    if args.kfold5:
        total_preds = kfold_total / kfold

    write_path = os.path.join(args.output_dir, "output.csv")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)    
    with open(write_path, 'w', encoding='utf8') as w:
        print("writing prediction : {}".format(write_path))
        w.write("id,prediction\n")
        for id, p in enumerate(total_preds):
            w.write('{},{}\n'.format(id,p))
            



def get_model(args):
    """
    Load model and move tensors to a given devices.
    """
    if args.model == 'lstm': model = LSTM(args)
    if args.model == 'lstmattn': model = LSTMATTN(args)
    if args.model == 'bert': model = Bert(args)
    

    model.to(args.device)

    return model


# 배치 전처리
def process_batch(batch, args):

    cate_batch = list(batch[:len(args.n_cate_cols)])
    numeric_batch = list(batch[len(args.n_cate_cols):-2])
    correct, mask = batch[-2:]
    
    # change to float
    mask = mask.type(torch.FloatTensor)
    correct = correct.type(torch.FloatTensor)
    #  interaction을 임시적으로 correct를 한칸 우측으로 이동한 것으로 사용
    #  saint의 경우 decoder에 들어가는 input이다
    interaction = correct + 1 # 패딩을 위해 correct값에 1을 더해준다.
    interaction = interaction * mask
    interaction = interaction.roll(shifts=1, dims=1)
    interaction[:, 0] = 0 # set padding index to the first sequence
    interaction = interaction.to(torch.int64)
    
    # categorical features
    for i in range(len(cate_batch)):
        cate_batch[i] = ((cate_batch[i] + 1) * mask).to(torch.int64).to(args.device)

    # numeric features
    # print(len(numeric_batch))
    # print(len(numeric_batch[4]))
    # print(len(numeric_batch[4][0]))
    # for i in range(3, len(numeric_batch)):
    #     numeric_batch[i] = numeric_batch[i].roll(shifts=1,dims=1)
    #     numeric_batch[i][:, 0] *= 0

    for i in range(len(numeric_batch)):
        numeric_batch[i] = (numeric_batch[i] * mask).to(torch.float).to(args.device)

    # gather index
    # 마지막 sequence만 사용하기 위한 index
    gather_index = torch.tensor(np.count_nonzero(mask, axis=1))
    gather_index = gather_index.view(-1, 1) - 1

    # 나머지 device memory로 이동
    correct = correct.to(args.device)
    mask = mask.to(args.device)
    interaction = interaction.to(args.device)
    gather_index = gather_index.to(args.device)

    return (*cate_batch, *numeric_batch,
             correct, mask, interaction, gather_index)


# loss계산하고 parameter update!
def compute_loss(preds, targets):
    """
    Args :
        preds   : (batch_size, max_seq_len)
        targets : (batch_size, max_seq_len)
    """
    loss = get_criterion(preds, targets)
    #마지막 시퀀드에 대한 값만 loss 계산
    loss = loss[:,-1]
    
    loss = torch.mean(loss)
    return loss

def update_params(loss, model, optimizer, args):
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), args.clip_grad)
    optimizer.step()
    optimizer.zero_grad()



def save_checkpoint(state, model_dir, model_filename):
    print('saving model ...\n')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)    
    torch.save(state, os.path.join(model_dir, model_filename))



def load_model(args):
    model_path = os.path.join(args.model_dir, args.model_name)
    print("Loading Model from:", model_path)
    load_state = torch.load(model_path)
    model = get_model(args)

    # 1. load model state
    model.load_state_dict(load_state['state_dict'], strict=True)
   
    
    print("Loading Model from:", model_path, "...Finished.")
    return model

def get_lr(optimizer):
    for param_group in optimizer.param_groups:
        return param_group['lr']