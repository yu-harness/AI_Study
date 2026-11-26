


def lm_loss(logits,labels,ignore = -100):
    return F.cross_entroenpy(logits.view(-1,logits.size(-1)),
                            labels.view(-1),
                            ignore_index = ignore)

# 预训练
labels = input_ids.clone()
labels[:,;-1] = input_ids[:,1:]
labels[:,-1] = -100

# STF 
labels[:,:prompt_len] = -100

