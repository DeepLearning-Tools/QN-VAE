import numpy as np
from torch.utils.data import DataLoader
import torch
from torch.optim import Adam
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from vq_vae import VQ_VAE
from trainer import Trainer


if __name__ == '__main__':
    batch_size = 256
    epochs = 10
    num_hidden = 128
    num_residual_hidden = 32
    num_residual_layers = 2
    embedding_dim = 64
    num_embeddings = 512
    commitment_cost = 0.25
    learning_rate = 1e-3

    quant_noise_probs = [0.25, 0.5, 0.75, 1]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    qn_model = dict()
    optimizer = dict()
    for q in quant_noise_probs:
        qn_model[q] = VQ_VAE(num_hidden, num_residual_layers, num_residual_hidden,
                             num_embeddings, embedding_dim, commitment_cost).to(device)
        optimizer[q] = Adam(qn_model[q].parameters(), lr=learning_rate, amsgrad=False)

    data = dict()
    data['train'] = datasets.CIFAR10(root="data", train=True, download=True,
                                     transform=transforms.Compose([
                                         transforms.ToTensor(),
                                         transforms.Normalize((0.5, 0.5, 0.5), (1.0, 1.0, 1.0))
                                     ]))
    data_variance = np.var(data['train'].data / 255.0)

    data['val'] = datasets.CIFAR10(root="data", train=False, download=True,
                                   transform=transforms.Compose([
                                       transforms.ToTensor(),
                                       transforms.Normalize((0.5, 0.5, 0.5), (1.0, 1.0, 1.0))
                                       ]))
    loader = dict()
    loader['train'] = DataLoader(data['train'], batch_size=batch_size, shuffle=True, pin_memory=True)
    loader['val'] = DataLoader(data['val'], batch_size=32, shuffle=True, pin_memory=True)

    for q in quant_noise_probs:
        trainer = Trainer(qn_model[q], optimizer[q], loader)
        trainer.data_variance = data_variance
        trainer.epochs = epochs
        trainer.run()
