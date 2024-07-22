import torch
import torch.nn as nn

class ShiftedCrossChunkAttention(nn.Module):
    def __init__(self, embed_dim, num_heads=8, shift_size=1):
        super(ShiftedCrossChunkAttention, self).__init__()
        self.attention = nn.MultiheadAttention(embed_dim=embed_dim, num_heads=num_heads)
        self.shift_size = shift_size

    def shift_key_value(self, embeddings, shift_size):
        # embeddings: Tensor of shape (chunk_size, num_chunks, embed_dim)
        #chunk_size, num_chunks, embed_dim = embeddings.size()
        
        # Shifting keys and values
        shifted_embeddings = torch.roll(embeddings, shifts=shift_size, dims=1)
        return shifted_embeddings

    def forward(self, chunk_embeddings):
        # chunk_embeddings: Tensor of shape (num_chunks, chunk_size, embed_dim)
        #num_chunks, chunk_size, embed_dim = chunk_embeddings.size()
        
        # Reshape for multihead attention
        chunk_embeddings = chunk_embeddings.permute(1, 0, 2)  # (chunk_size, num_chunks, embed_dim)
        
        # Shift keys and values
        shifted_embeddings = self.shift_key_value(chunk_embeddings, self.shift_size)
        
        # Apply attention mechanism across shifted chunks
        attn_output, _ = self.attention(chunk_embeddings, shifted_embeddings, shifted_embeddings)
        
        # Reshape back to original format
        attn_output = attn_output.permute(1, 0, 2)  # (num_chunks, chunk_size, embed_dim)
        
        return attn_output
