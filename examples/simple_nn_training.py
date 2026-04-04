"""Simple example: Train a neural network with Butterfly layers on MNIST.

This shows how to use torch_butterfly.Butterfly as a drop-in replacement
for nn.Linear, giving O(n log n) parameters instead of O(n^2).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from torch_butterfly import Butterfly


class ButterflyNet(nn.Module):
    """A simple 3-layer network using Butterfly layers for classification."""

    def __init__(self, in_size=784, hidden_size=512, num_classes=10):
        super().__init__()
        self.layers = nn.Sequential(
            # Butterfly as a drop-in replacement for nn.Linear(784, 512)
            Butterfly(in_size, hidden_size, bias=True),
            nn.ReLU(),
            # Another Butterfly layer: hidden -> hidden
            Butterfly(hidden_size, hidden_size, bias=True),
            nn.ReLU(),
            # Final linear projection to class logits
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x):
        return self.layers(x)


def make_fake_mnist(n_train=1024, n_test=256):
    """Create random data shaped like MNIST for a self-contained example."""
    x_train = torch.randn(n_train, 784)
    y_train = torch.randint(0, 10, (n_train,))
    x_test = torch.randn(n_test, 784)
    y_test = torch.randint(0, 10, (n_test,))
    return (
        DataLoader(TensorDataset(x_train, y_train), batch_size=64, shuffle=True),
        DataLoader(TensorDataset(x_test, y_test), batch_size=64),
    )


def train(model, train_loader, optimizer, epoch):
    model.train()
    total_loss = 0.0
    for x, y in train_loader:
        optimizer.zero_grad()
        loss = F.cross_entropy(model(x), y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    avg = total_loss / len(train_loader)
    print(f"Epoch {epoch}: train loss = {avg:.4f}")


@torch.no_grad()
def evaluate(model, test_loader):
    model.eval()
    correct = total = 0
    for x, y in test_loader:
        correct += (model(x).argmax(dim=1) == y).sum().item()
        total += y.size(0)
    acc = correct / total
    print(f"  test accuracy = {acc:.2%}")
    return acc


def main():
    torch.manual_seed(42)

    # -- Data --
    # Using fake data so this example runs without downloading anything.
    # Replace with torchvision.datasets.MNIST for real training.
    train_loader, test_loader = make_fake_mnist()

    # -- Model --
    model = ButterflyNet(in_size=784, hidden_size=512, num_classes=10)

    # Count parameters: Butterfly layers have O(n log n) params vs O(n^2)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"ButterflyNet parameters: {n_params:,}")

    # Compare with an equivalent dense network
    dense = nn.Sequential(
        nn.Linear(784, 512), nn.ReLU(),
        nn.Linear(512, 512), nn.ReLU(),
        nn.Linear(512, 10),
    )
    n_dense = sum(p.numel() for p in dense.parameters())
    print(f"Dense equivalent parameters: {n_dense:,}")
    print(f"Compression ratio: {n_dense / n_params:.1f}x\n")

    # -- Training --
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(1, 6):
        train(model, train_loader, optimizer, epoch)
        evaluate(model, test_loader)

    print("\nDone! The Butterfly layers learned just like nn.Linear,")
    print("but with far fewer parameters.")


if __name__ == "__main__":
    main()
