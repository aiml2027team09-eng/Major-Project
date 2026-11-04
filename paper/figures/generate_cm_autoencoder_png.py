import os
import numpy as np
import matplotlib.pyplot as plt

def generate_cicids2018_cm():
    # Primary Benchmark: CSE-CIC-IDS2018 Standalone Autoencoder
    # Actual Benign: 86,556 -> Pred Benign: 77,877 (0.90), Pred Attack: 8,679 (0.10)
    # Actual Attack: 14,114 -> Pred Benign: 42 (0.00), Pred Attack: 14,072 (1.00)
    cm_norm = np.array([
        [0.8997, 0.1003],
        [0.0030, 0.9970]
    ])
    labels = ['Benign', 'Attack']
    
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cax = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues, vmin=0.0, vmax=1.0)
    
    cbar = fig.colorbar(cax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=10)
    
    ax.set(
        xticks=np.arange(cm_norm.shape[1]),
        yticks=np.arange(cm_norm.shape[0]),
        xticklabels=labels,
        yticklabels=labels,
        title='Normalized Confusion Matrix - Autoencoder (CICIDS2018)',
        ylabel='True Class',
        xlabel='Predicted Class'
    )
    
    ax.title.set_fontsize(12)
    ax.xaxis.label.set_fontsize(11)
    ax.yaxis.label.set_fontsize(11)
    ax.tick_params(axis='both', which='major', labelsize=10)
    
    # Loop over data dimensions and create text annotations.
    thresh = cm_norm.max() / 2.
    for i in range(cm_norm.shape[0]):
        for j in range(cm_norm.shape[1]):
            val = cm_norm[i, j]
            ax.text(j, i, f"{val:.2f}",
                    ha="center", va="center",
                    color="white" if val > thresh else "black",
                    fontsize=12, fontweight='medium')
            
    fig.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), "cm_autoencoder_cicids2018.png")
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {output_path}")

def generate_nsl_kdd_cm():
    # Secondary Benchmark: NSL-KDD Standalone Autoencoder
    # Actual Normal: 11,538 -> Pred Normal: 10,669 (0.92), Pred Attack: 869 (0.08)
    # Actual Attack: 10,631 -> Pred Normal: 730 (0.07), Pred Attack: 9,901 (0.93)
    cm_norm = np.array([
        [0.9247, 0.0753],
        [0.0687, 0.9313]
    ])
    labels = ['Normal', 'Attack']
    
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cax = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues, vmin=0.0, vmax=1.0)
    
    cbar = fig.colorbar(cax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=10)
    
    ax.set(
        xticks=np.arange(cm_norm.shape[1]),
        yticks=np.arange(cm_norm.shape[0]),
        xticklabels=labels,
        yticklabels=labels,
        title='Normalized Confusion Matrix - Autoencoder (NSL_KDD)',
        ylabel='True Class',
        xlabel='Predicted Class'
    )
    
    ax.title.set_fontsize(12)
    ax.xaxis.label.set_fontsize(11)
    ax.yaxis.label.set_fontsize(11)
    ax.tick_params(axis='both', which='major', labelsize=10)
    
    thresh = cm_norm.max() / 2.
    for i in range(cm_norm.shape[0]):
        for j in range(cm_norm.shape[1]):
            val = cm_norm[i, j]
            ax.text(j, i, f"{val:.2f}",
                    ha="center", va="center",
                    color="white" if val > thresh else "black",
                    fontsize=12, fontweight='medium')
            
    fig.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), "cm_autoencoder_nsl_kdd.png")
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated: {output_path}")

if __name__ == "__main__":
    generate_cicids2018_cm()
    generate_nsl_kdd_cm()
