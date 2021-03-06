import torch
import model
import torch.optim as optim
import torch.nn as nn
import TrafficDataLoader
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

### setup hyperparameters
lr = 3e-4
z_dim = 100 # fix it
input_dim = 1259 # fix it
batch_size = 4096
num_epochs = 1000
step = 0

def setup_gpu():
    return "cuda" if torch.cuda.is_available() else "cpu"

def denormalize(x):
    return 0.5 * (x * 200000 - x * 0 + 200000 + 0)

device = setup_gpu()
print("USE GPU : {}".format(device))

### model load
discriminator = model.Discriminator_V2(input_dim).to(device=device)
generator = model.Generator_V2(z_dim, input_dim).to(device=device)
optimizer_discriminator = optim.Adam(discriminator.parameters(), lr=lr)
optimizer_generator = optim.Adam(generator.parameters(), lr=lr)
criterion = nn.BCELoss().cuda()

fixed_noise = torch.randn((batch_size, z_dim)).to(device)
fixed_noise = denormalize(fixed_noise)
### dataset
amazon_dataset = TrafficDataLoader.AmazonPrimeDataset('dataset/reformat_amazon/static')
loader = DataLoader(amazon_dataset, batch_size=batch_size, shuffle=True)

print("start training")
for epoch in range(num_epochs):
    print("start epoch : {}".format(epoch))
    for batch_idx, real in enumerate(loader):

        real = real.to(device)
        batch_size = real.shape[0]
        ### train Discriminator
        noise = torch.randn(batch_size, z_dim).to(device)
        noise = denormalize(noise)
        fake = generator(noise)
        # fake = torch.abs(fake)
        print(real.shape)
        discriminator_real = discriminator(real)
        lossD_real = criterion(discriminator_real, torch.ones_like(discriminator_real))
        discriminator_fake = discriminator(fake)
        lossD_fake = criterion(discriminator_fake, torch.ones_like(discriminator_fake))
        lossD = (lossD_real + lossD_fake)/2
        discriminator.zero_grad()
        lossD.backward(retain_graph=True)
        optimizer_discriminator.step()
        ### train generator
        output = discriminator(fake)
        lossG = criterion(output, torch.ones_like(output))
        generator.zero_grad()
        lossG.backward()
        optimizer_generator.step()

        if batch_idx == 0:
            print(
                f"Epoch [{epoch}/{num_epochs}] Batch {batch_idx}/{len(loader)} \
                              Loss D: {lossD:.4f}, loss G: {lossG:.4f}"
            )
            with torch.no_grad():
                fake_rand = generator(denormalize(torch.randn((batch_size, z_dim)).to(device))).cpu()
                fake = generator(fixed_noise).cpu()
                data = real.cpu()
                # fake = torch.abs(fake)
                # fake_rand = torch.abs(fake_rand)
                plt.figure(figsize=(24, 12))
                plt.title('fake_fixed')
                plt.plot(fake[0])
                plt.savefig('dataset/reformat_amazon/result_V2/fake/fake_{}.png'.format(step))
                plt.show()
                plt.figure(figsize=(24, 12))
                plt.title('fake_random')
                plt.plot(fake_rand[0])
                plt.savefig('dataset/reformat_amazon/result_V2/fake/fake_rand_{}.png'.format(step))
                plt.show()
                plt.figure(figsize=(24, 12))
                plt.title('real')
                plt.plot(data[0])
                plt.savefig('dataset/reformat_amazon/result_V2/real/real_{}.png'.format(step))
                plt.show()
                step += 1

    if epoch % 10 == 0:
        torch.save({
            'epoch': epoch,
            'generator': generator,
            'discriminator': discriminator,
            'generator_state_dict': generator.state_dict(),
            'discriminator_state_dict': discriminator.state_dict(),
        }, "dataset/reformat_amazon/result_V2/checkpoints/model_checkpoint_{}.pt".format(epoch))

