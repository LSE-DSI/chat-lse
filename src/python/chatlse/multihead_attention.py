import torch
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, embed_dim, num_heads=16):
        super(MultiHeadAttention, self).__init__()
        self.attention = nn.MultiheadAttention(embed_dim=embed_dim, num_heads=num_heads)

    def forward(self, chunk_embeddings):

        # Reshape for multihead attention
        chunk_embeddings = chunk_embeddings.permute(1, 0, 2)  # (chunk_size, num_chunks, embed_dim)

        # Apply attention mechanism across chunks
        attn_output, _ = self.attention(chunk_embeddings, chunk_embeddings, chunk_embeddings)

        # Reshape back to original format
        attn_output = attn_output.permute(1, 0, 2)  # (num_chunks, chunk_size, embed_dim)

        return attn_output

