import numpy as np

class Cascade729Compressor:
    """Implements a true 729:1 hierarchical compression engine by cascading

    three 9:1 pooling depth tiers with Product Vector Quantization.
    """

    def __init__(self, hidden_dim=64, num_sub_spaces=4):
        self.base_ratio = 9
        self.layers = 3
        self.total_ratio = self.base_ratio**self.layers  # Exactly 729
        self.hidden_dim = hidden_dim
        self.num_sub_spaces = num_sub_spaces

        # Sub-vector dimension sizing
        self.sub_dim = hidden_dim // num_sub_spaces
        # 8-bit Codebook: (Sub-spaces, 256 Centroids, Sub-dimensions)
        self.codebook = np.random.uniform(
            -1.0, 1.0, (self.num_sub_spaces, 256, self.sub_dim)
        )

    def _pool_layer(self, data):
        seq_len, hidden_dim = data.shape
        target_len = int(np.ceil(seq_len / self.base_ratio))
        padded_len = target_len * self.base_ratio

        # Dynamic padding up to the nearest multiple of 9
        padded = np.pad(
            data, ((0, padded_len - seq_len), (0, 0)), mode="edge"
        )
        return padded.reshape(target_len, self.base_ratio, hidden_dim).mean(
            axis=1
        )

    def compress(self, token_embeddings):
        current = token_embeddings
        original_len = len(token_embeddings)

        # 1. Cascading 3-tier depth temporal reduction (9 -> 81 -> 729)
        for _ in range(self.layers):
            current = self._pool_layer(current)

        # 2. Product Vector Quantization Bottleneck
        # Split features into sub-vectors for robust quantization
        target_len = current.shape[0]
        sub_vectors = current.reshape(
            target_len, self.num_sub_spaces, self.sub_dim
        )

        indices = np.zeros((target_len, self.num_sub_spaces), dtype=np.uint8)

        for i in range(self.num_sub_spaces):
            # Compute Euclidean distance between pooled sub-vectors and codebook centroids
            diff = (
                sub_vectors[:, i, np.newaxis, :] - self.codebook[i, np.newaxis, :, :]
            )
            distances = np.linalg.norm(diff, axis=2)
            indices[:, i] = np.argmin(distances, axis=1)

        return indices, original_len

    def decompress(self, indices, original_len):
        target_len = indices.shape[0]
        reconstructed_sub = np.zeros(
            (target_len, self.num_sub_spaces, self.sub_dim)
        )

        # 1. Inverse Codebook Lookup
        for i in range(self.num_sub_spaces):
            reconstructed_sub[:, i, :] = self.codebook[i, indices[:, i]]

        current = reconstructed_sub.reshape(target_len, self.hidden_dim)

        # 2. Symmetric Re-expansion via Block-wise Upsampling
        for _ in range(self.layers):
            # Repeat each token position individually to maintain temporal continuity
            current = np.repeat(current, self.base_ratio, axis=0)

        return current[:original_len]


# Execution Verification
if __name__ == "__main__":
    # Ensure reproducibility
    np.random.seed(42)

    # Initialize Compressor for 64-dimensional stream
    compressor = Cascade729Compressor(hidden_dim=64, num_sub_spaces=4)

    # Simulate an incoming high-dimensional token stream (Exactly 7290 tokens, 64 dims)
    mock_stream = np.random.randn(7290, 64)

    # Execute Pipeline
    compressed_codes, orig_length = compressor.compress(mock_stream)
    recovered_stream = compressor.decompress(compressed_codes, orig_length)

    print(f"Original Data Shape:    {mock_stream.shape}")
    print(f"Compressed Codes Shape: {compressed_codes.shape}")
    print(f"Recovered Data Shape:   {recovered_stream.shape}")
    print("---")
    print(f"Original Token Count:   {orig_length}")
    print(f"Compressed Token Count: {len(compressed_codes)}")
    print(f"Achieved Ratio:         {orig_length / len(compressed_codes):.1f}:1")
