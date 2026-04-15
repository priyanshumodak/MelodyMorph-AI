import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import torch.nn as nn
from models.gan import Generator
from models.wgan import Critic

# Hyperparameters
epochs = 200
batch_size = 32
noise_dim = 100
clip_value = 0.01

G = Generator()
C = Critic()

opt_G = torch.optim.RMSprop(G.parameters(), lr=0.00005)
opt_C = torch.optim.RMSprop(C.parameters(), lr=0.00005)

real_data = torch.randn(1000, 128)

for epoch in range(epochs):
    for i in range(0, len(real_data), batch_size):
        real = real_data[i:i+batch_size]

        # Train Critic
        noise = torch.randn(real.size(0), noise_dim)
        fake = G(noise)

        loss_C = -(torch.mean(C(real)) - torch.mean(C(fake)))

        opt_C.zero_grad()
        loss_C.backward()
        opt_C.step()

        # Weight clipping
        for p in C.parameters():
            p.data.clamp_(-clip_value, clip_value)

        # Train Generator
        if i % 5 == 0:
            fake = G(noise)
            loss_G = -torch.mean(C(fake))

            opt_G.zero_grad()
            loss_G.backward()
            opt_G.step()

    print(f"Epoch {epoch} | C Loss: {loss_C.item():.4f} | G Loss: {loss_G.item():.4f}")

# Save model
torch.save(G.state_dict(), "generator_wgan.pth")
print("✅ WGAN Training Complete")