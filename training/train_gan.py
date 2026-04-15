import torch
import torch.nn as nn
import numpy as np
from models.gan import Generator, Discriminator

# Hyperparameters
noise_dim = 100
data_dim = 128
epochs = 200
batch_size = 32

# Models
G = Generator()
D = Discriminator()

criterion = nn.BCELoss()
opt_G = torch.optim.Adam(G.parameters(), lr=0.0002)
opt_D = torch.optim.Adam(D.parameters(), lr=0.0002)

# Dummy dataset (for now)
real_data = torch.randn(1000, data_dim)

for epoch in range(epochs):
    for i in range(0, len(real_data), batch_size):
        real = real_data[i:i+batch_size]

        # Train Discriminator
        noise = torch.randn(real.size(0), noise_dim)
        fake = G(noise)

        D_real = D(real)
        D_fake = D(fake.detach())

        loss_D = -torch.mean(torch.log(D_real) + torch.log(1 - D_fake))

        opt_D.zero_grad()
        loss_D.backward()
        opt_D.step()

        # Train Generator
        D_fake = D(fake)
        loss_G = -torch.mean(torch.log(D_fake))

        opt_G.zero_grad()
        loss_G.backward()
        opt_G.step()

    print(f"Epoch {epoch} | D Loss: {loss_D.item():.4f} | G Loss: {loss_G.item():.4f}")

# Save model
torch.save(G.state_dict(), "generator.pth")
print("✅ Training Complete. Model saved.")