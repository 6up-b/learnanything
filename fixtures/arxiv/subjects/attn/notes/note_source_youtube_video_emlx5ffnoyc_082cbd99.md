---
schema_version: 1
id: note_source_youtube_video_emlx5ffnoyc_082cbd99
subjects:
  - attn
related_los: []
related_concepts: []
source_type: canonical_source
canonical_source:
  kind: youtube_video
  original_uri: https://www.youtube.com/watch?v=eMlx5fFNoYc
  canonical_uri: https://www.youtube.com/watch?v=eMlx5fFNoYc
  title: YouTube video eMlx5fFNoYc
  authors: []
  retrieved_at: '2026-05-28T20:28:22Z'
  content_hash: 
    sha256:082cbd9964b7ea1d51e6064820b714416a2bb63e675d5ced1295ae9bddc4c64a
  license_hint:
created_at: '2026-05-28T20:28:22Z'
updated_at: '2026-05-28T20:28:22Z'
---

# YouTube video eMlx5fFNoYc

[t=0.0-2.0] In the last chapter, you and I started to step

[t=2.0-4.0] through the internal workings of a transformer.

[t=4.6-7.9] This is one of the key pieces of technology inside large language models,

[t=7.9-10.2] and a lot of other tools in the modern wave of AI.

[t=11.0-15.5] It first hit the scene in a now-famous 2017 paper called Attention is All You Need,

[t=15.5-19.8] and in this chapter you and I will dig into what this attention mechanism is,

[t=19.8-21.7] visualizing how it processes data.

[t=26.1-29.5] As a quick recap, here's the important context I want you to have in mind.

[t=30.0-33.0] The goal of the model that you and I are studying is to

[t=33.0-36.1] take in a piece of text and predict what word comes next.

[t=36.9-40.3] The input text is broken up into little pieces that we call tokens,

[t=40.3-43.0] and these are very often words or pieces of words,

[t=43.0-47.2] but just to make the examples in this video easier for you and me to think about,

[t=47.2-50.6] let's simplify by pretending that tokens are always just words.

[t=51.5-54.5] The first step in a transformer is to associate each token

[t=54.5-57.7] with a high-dimensional vector, what we call its embedding.

[t=57.7-62.0] The most important idea I want you to have in mind is how directions in this

[t=62.0-67.0] high-dimensional space of all possible embeddings can correspond with semantic meaning.

[t=67.7-71.7] In the last chapter we saw an example for how direction can correspond to gender,

[t=71.7-75.5] in the sense that adding a certain step in this space can take you from the

[t=75.5-79.6] embedding of a masculine noun to the embedding of the corresponding feminine noun.

[t=80.2-83.6] That's just one example you could imagine how many other directions in this

[t=83.6-87.6] high-dimensional space could correspond to numerous other aspects of a word's meaning.

[t=88.8-92.5] The aim of a transformer is to progressively adjust these embeddings

[t=92.5-95.4] so that they don't merely encode an individual word,

[t=95.4-99.2] but instead they bake in some much, much richer contextual meaning.

[t=100.1-103.7] I should say up front that a lot of people find the attention mechanism,

[t=103.7-106.1] this key piece in a transformer, very confusing,

[t=106.0-109.0] so don't worry if it takes some time for things to sink in.

[t=109.4-112.7] I think that before we dive into the computational details and all

[t=112.7-115.8] the matrix multiplications, it's worth thinking about a couple

[t=115.8-119.2] examples for the kind of behavior that we want attention to enable.

[t=120.1-124.3] Consider the phrases American shrew mole, one mole of carbon dioxide,

[t=124.3-126.2] and take a biopsy of the mole.

[t=126.7-130.0] You and I know that the word mole has different meanings in each one of these,

[t=130.0-130.9] based on the context.

[t=131.4-135.1] But after the first step of a transformer, the one that breaks up the text

[t=135.1-138.8] and associates each token with a vector, the vector that's associated with

[t=138.8-141.2] mole would be the same in all of these cases,

[t=141.2-144.9] because this initial token embedding is effectively a lookup table with no

[t=144.9-146.2] reference to the context.

[t=146.6-150.0] It's only in the next step of the transformer that the surrounding

[t=150.0-153.1] embeddings have the chance to pass information into this one.

[t=153.8-158.3] The picture you might have in mind is that there are multiple distinct directions in

[t=158.3-162.5] this embedding space encoding the multiple distinct meanings of the word mole,

[t=162.5-167.1] and that a well-trained attention block calculates what you need to add to the generic

[t=167.1-171.8] embedding to move it to one of these specific directions, as a function of the context.

[t=173.3-176.2] To take another example, consider the embedding of the word tower.

[t=177.1-181.1] This is presumably some very generic, non-specific direction in the space,

[t=181.1-183.7] associated with lots of other large, tall nouns.

[t=184.0-186.6] If this word was immediately preceded by Eiffel,

[t=186.6-190.3] you could imagine wanting the mechanism to update this vector so that

[t=190.3-194.3] it points in a direction that more specifically encodes the Eiffel tower,

[t=194.3-199.1] maybe correlated with vectors associated with Paris and France and things made of steel.

[t=199.9-202.2] If it was also preceded by the word miniature,

[t=202.2-204.6] then the vector should be updated even further,

[t=204.6-207.5] so that it no longer correlates with large, tall things.

[t=209.5-212.3] More generally than just refining the meaning of a word,

[t=212.3-215.7] the attention block allows the model to move information encoded in

[t=215.7-219.5] one embedding to that of another, potentially ones that are quite far away,

[t=219.5-223.3] and potentially with information that's much richer than just a single word.

[t=223.3-227.9] What we saw in the last chapter was how after all of the vectors flow through the

[t=227.9-230.9] network, including many different attention blocks,

[t=230.9-235.7] the computation you perform to produce a prediction of the next token is entirely a

[t=235.7-238.3] function of the last vector in the sequence.

[t=239.1-243.4] Imagine, for example, that the text you input is most of an entire mystery novel,

[t=243.4-247.8] all the way up to a point near the end, which reads, therefore the murderer was.

[t=248.4-251.5] If the model is going to accurately predict the next word,

[t=251.5-256.0] that final vector in the sequence, which began its life simply embedding the word was,

[t=256.0-260.3] will have to have been updated by all of the attention blocks to represent much,

[t=260.3-264.3] much more than any individual word, somehow encoding all of the information

[t=264.3-268.2] from the full context window that's relevant to predicting the next word.

[t=269.5-272.6] To step through the computations, though, let's take a much simpler example.

[t=273.0-275.4] Imagine that the input includes the phrase, a

[t=275.4-278.0] fluffy blue creature roamed the verdant forest.

[t=278.5-282.6] And for the moment, suppose that the only type of update that we care about

[t=282.6-286.8] is having the adjectives adjust the meanings of their corresponding nouns.

[t=287.0-290.7] What I'm about to describe is what we would call a single head of attention,

[t=290.7-294.9] and later we will see how the attention block consists of many different heads run in

[t=294.9-295.4] parallel.

[t=296.1-299.8] Again, the initial embedding for each word is some high dimensional vector

[t=299.8-303.4] that only encodes the meaning of that particular word with no context.

[t=304.0-305.2] Actually, that's not quite true.

[t=305.4-307.6] They also encode the position of the word.

[t=308.0-311.6] There's a lot more to say about the specific way that positions are encoded,

[t=311.6-315.2] but right now, all you need to know is that the entries of this vector are

[t=315.2-318.9] enough to tell you both what the word is and where it exists in the context.

[t=319.5-321.7] Let's go ahead and denote these embeddings with the letter e.

[t=322.4-326.1] The goal is to have a series of computations produce a new refined

[t=326.1-329.6] set of embeddings where, for example, those corresponding to the

[t=329.6-333.4] nouns have ingested the meaning from their corresponding adjectives.

[t=333.9-337.1] And playing the deep learning game, we want most of the computations

[t=337.1-339.3] involved to look like matrix-vector products,

[t=339.3-341.7] where the matrices are full of tuneable weights,

[t=341.7-344.0] things that the model will learn based on data.

[t=344.7-348.4] To be clear, I'm making up this example of adjectives updating nouns just to

[t=348.4-352.3] illustrate the type of behavior that you could imagine an attention head doing.

[t=352.9-357.0] As with so much deep learning, the true behavior is much harder to parse because it's

[t=357.0-361.3] based on tweaking and tuning a huge number of parameters to minimize some cost function.

[t=361.7-365.6] It's just that as we step through all of different matrices filled with parameters

[t=365.6-369.5] that are involved in this process, I think it's really helpful to have an imagined

[t=369.5-373.2] example of something that it could be doing to help keep it all more concrete.

[t=374.1-378.2] For the first step of this process, you might imagine each noun, like creature,

[t=378.2-382.0] asking the question, hey, are there any adjectives sitting in front of me?

[t=382.2-385.4] And for the words fluffy and blue, to each be able to answer,

[t=385.4-388.0] yeah, I'm an adjective and I'm in that position.

[t=389.0-392.3] That question is somehow encoded as yet another vector,

[t=392.3-396.1] another list of numbers, which we call the query for this word.

[t=397.0-402.0] This query vector though has a much smaller dimension than the embedding vector, say 128.

[t=402.9-406.3] Computing this query looks like taking a certain matrix,

[t=406.3-409.8] which I'll label wq, and multiplying it by the embedding.

[t=411.0-414.2] Compressing things a bit, let's write that query vector as q,

[t=414.2-418.0] and then anytime you see me put a matrix next to an arrow like this one,

[t=418.0-422.6] it's meant to represent that multiplying this matrix by the vector at the arrow's start

[t=422.6-424.8] gives you the vector at the arrow's end.

[t=425.9-430.2] In this case, you multiply this matrix by all of the embeddings in the context,

[t=430.2-432.6] producing one query vector for each token.

[t=433.7-436.4] The entries of this matrix are parameters of the model,

[t=436.4-439.7] which means the true behavior is learned from data, and in practice,

[t=439.7-443.4] what this matrix does in a particular attention head is challenging to parse.

[t=443.9-447.9] But for our sake, imagining an example that we might hope that it would learn,

[t=447.9-451.4] we'll suppose that this query matrix maps the embeddings of nouns to

[t=451.4-454.9] certain directions in this smaller query space that somehow encodes

[t=454.9-458.0] the notion of looking for adjectives in preceding positions.

[t=458.8-461.4] As to what it does to other embeddings, who knows?

[t=461.7-464.3] Maybe it simultaneously tries to accomplish some other goal with those.

[t=464.5-467.2] Right now, we're laser focused on the nouns.

[t=467.3-471.6] At the same time, associated with this is a second matrix called the key matrix,

[t=471.6-474.6] which you also multiply by every one of the embeddings.

[t=475.3-478.5] This produces a second sequence of vectors that we call the keys.

[t=479.4-483.1] Conceptually, you want to think of the keys as potentially answering the queries.

[t=483.8-488.0] This key matrix is also full of tuneable parameters, and just like the query matrix,

[t=488.0-491.4] it maps the embedding vectors to that same smaller dimensional space.

[t=492.2-497.0] You think of the keys as matching the queries whenever they closely align with each other.

[t=497.5-502.2] In our example, you would imagine that the key matrix maps the adjectives like fluffy and

[t=502.2-506.7] blue to vectors that are closely aligned with the query produced by the word creature.

[t=507.2-510.1] To measure how well each key matches each query,

[t=510.1-514.0] you compute a dot product between each possible key-query pair.

[t=514.5-517.1] I like to visualize a grid full of a bunch of dots,

[t=517.1-520.2] where the bigger dots correspond to the larger dot products,

[t=520.2-522.6] the places where the keys and queries align.

[t=523.3-527.5] For our adjective noun example, that would look a little more like this,

[t=527.5-532.4] where if the keys produced by fluffy and blue really do align closely with the query

[t=532.4-537.3] produced by creature, then the dot products in these two spots would be some large

[t=537.3-538.3] positive numbers.

[t=539.1-542.3] In the lingo, machine learning people would say that this means the

[t=542.3-545.4] embeddings of fluffy and blue attend to the embedding of creature.

[t=546.0-549.5] By contrast to the dot product between the key for some other

[t=549.5-552.9] word like the and the query for creature would be some small

[t=552.9-556.6] or negative value that reflects that are unrelated to each other.

[t=557.7-561.3] So we have this grid of values that can be any real number from

[t=561.3-565.1] negative infinity to infinity, giving us a score for how relevant

[t=565.1-568.5] each word is to updating the meaning of every other word.

[t=569.2-572.5] The way we're about to use these scores is to take a certain

[t=572.5-575.8] weighted sum along each column, weighted by the relevance.

[t=576.5-580.2] So instead of having values range from negative infinity to infinity,

[t=580.2-584.0] what we want is for the numbers in these columns to be between 0 and 1,

[t=584.0-588.2] and for each column to add up to 1, as if they were a probability distribution.

[t=589.3-592.2] If you're coming in from the last chapter, you know what we need to do then.

[t=592.6-597.3] We compute a softmax along each one of these columns to normalize the values.

[t=600.1-603.2] In our picture, after you apply softmax to all of the columns,

[t=603.2-605.9] we'll fill in the grid with these normalized values.

[t=606.8-610.7] At this point you're safe to think about each column as giving weights according

[t=610.7-614.6] to how relevant the word on the left is to the corresponding value at the top.

[t=615.1-616.8] We call this grid an attention pattern.

[t=618.1-620.2] Now if you look at the original transformer paper,

[t=620.2-622.8] there's a really compact way that they write this all down.

[t=623.9-627.4] Here the variables q and k represent the full arrays of query

[t=627.4-631.0] and key vectors respectively, those little vectors you get by

[t=631.0-634.6] multiplying the embeddings by the query and the key matrices.

[t=635.2-639.1] This expression up in the numerator is a really compact way to represent

[t=639.1-643.0] the grid of all possible dot products between pairs of keys and queries.

[t=644.0-648.0] A small technical detail that I didn't mention is that for numerical stability,

[t=648.0-651.2] it happens to be helpful to divide all of these values by the

[t=651.2-654.0] square root of the dimension in that key query space.

[t=654.5-657.8] Then this softmax that's wrapped around the full expression

[t=657.8-660.8] is meant to be understood to apply column by column.

[t=661.6-664.7] As to that v term, we'll talk about it in just a second.

[t=665.0-668.5] Before that, there's one other technical detail that so far I've skipped.

[t=669.0-673.0] During the training process, when you run this model on a given text example,

[t=673.0-677.4] and all of the weights are slightly adjusted and tuned to either reward or punish it

[t=677.4-681.5] based on how high a probability it assigns to the true next word in the passage,

[t=681.5-685.4] it turns out to make the whole training process a lot more efficient if you

[t=685.4-689.6] simultaneously have it predict every possible next token following each initial

[t=689.6-691.6] subsequence of tokens in this passage.

[t=691.9-694.9] For example, with the phrase that we've been focusing on,

[t=694.9-699.1] it might also be predicting what words follow creature and what words follow the.

[t=699.9-702.8] This is really nice, because it means what would otherwise

[t=702.8-705.6] be a single training example effectively acts as many.

[t=706.1-709.4] For the purposes of our attention pattern, it means that you never

[t=709.4-712.2] want to allow later words to influence earlier words,

[t=712.2-716.0] since otherwise they could kind of give away the answer for what comes next.

[t=716.6-719.6] What this means is that we want all of these spots here,

[t=719.6-722.8] the ones representing later tokens influencing earlier ones,

[t=722.8-724.6] to somehow be forced to be zero.

[t=725.9-728.7] The simplest thing you might think to do is to set them equal to zero,

[t=728.7-731.3] but if you did that the columns wouldn't add up to one anymore,

[t=731.3-732.4] they wouldn't be normalized.

[t=733.1-736.4] So instead, a common way to do this is that before applying softmax,

[t=736.4-739.0] you set all of those entries to be negative infinity.

[t=739.7-743.6] If you do that, then after applying softmax, all of those get turned into zero,

[t=743.6-745.2] but the columns stay normalized.

[t=746.0-747.5] This process is called masking.

[t=747.5-751.3] There are versions of attention where you don't apply it, but in our GPT example,

[t=751.3-754.9] even though this is more relevant during the training phase than it would be,

[t=754.9-757.4] say, running it as a chatbot or something like that,

[t=757.4-761.5] you do always apply this masking to prevent later tokens from influencing earlier ones.

[t=762.5-765.8] Another fact that's worth reflecting on about this attention

[t=765.8-769.5] pattern is how its size is equal to the square of the context size.

[t=769.9-774.0] So this is why context size can be a really huge bottleneck for large language models,

[t=774.0-775.6] and scaling it up is non-trivial.

[t=776.3-780.1] As you imagine, motivated by a desire for bigger and bigger context windows,

[t=780.1-784.1] recent years have seen some variations to the attention mechanism aimed at making

[t=784.1-788.3] context more scalable, but right here, you and I are staying focused on the basics.

[t=790.6-792.9] Okay, great, computing this pattern lets the model

[t=792.9-795.5] deduce which words are relevant to which other words.

[t=796.0-798.5] Now you need to actually update the embeddings,

[t=798.5-802.8] allowing words to pass information to whichever other words they're relevant to.

[t=802.8-806.8] For example, you want the embedding of Fluffy to somehow cause a change

[t=806.8-810.8] to Creature that moves it to a different part of this 12,000-dimensional

[t=810.8-814.5] embedding space that more specifically encodes a Fluffy creature.

[t=815.5-818.3] What I'm going to do here is first show you the most straightforward

[t=818.3-820.9] way that you could do this, though there's a slight way that

[t=820.9-823.5] this gets modified in the context of multi-headed attention.

[t=824.1-827.1] This most straightforward way would be to use a third matrix,

[t=827.1-831.4] what we call the value matrix, which you multiply by the embedding of that first word,

[t=831.4-832.4] for example Fluffy.

[t=833.3-835.9] The result of this is what you would call a value vector,

[t=835.9-839.2] and this is something that you add to the embedding of the second word,

[t=839.2-841.9] in this case something you add to the embedding of Creature.

[t=842.6-847.0] So this value vector lives in the same very high-dimensional space as the embeddings.

[t=847.5-850.8] When you multiply this value matrix by the embedding of a word,

[t=850.8-855.3] you might think of it as saying, if this word is relevant to adjusting the meaning of

[t=855.3-859.8] something else, what exactly should be added to the embedding of that something else

[t=859.8-861.2] in order to reflect this?

[t=862.1-866.0] Looking back in our diagram, let's set aside all of the keys and the queries,

[t=866.0-869.4] since after you compute the attention pattern you're done with those,

[t=869.4-872.9] then you're going to take this value matrix and multiply it by every

[t=872.9-876.1] one of those embeddings to produce a sequence of value vectors.

[t=877.1-879.1] You might think of these value vectors as being

[t=879.1-881.1] kind of associated with the corresponding keys.

[t=882.3-885.8] For each column in this diagram, you multiply each of the

[t=885.8-889.2] value vectors by the corresponding weight in that column.

[t=890.1-892.8] For example here, under the embedding of Creature,

[t=892.8-897.1] you would be adding large proportions of the value vectors for Fluffy and Blue,

[t=897.1-901.6] while all of the other value vectors get zeroed out, or at least nearly zeroed out.

[t=902.1-906.8] And then finally, the way to actually update the embedding associated with this column,

[t=906.8-909.9] previously encoding some context-free meaning of Creature,

[t=909.9-913.1] you add together all of these rescaled values in the column,

[t=913.1-916.7] producing a change that you want to add, that I'll label delta-e,

[t=916.7-919.3] and then you add that to the original embedding.

[t=919.7-923.1] Hopefully what results is a more refined vector encoding the more

[t=923.1-926.5] contextually rich meaning, like that of a fluffy blue creature.

[t=927.4-930.2] And of course you don't just do this to one embedding,

[t=930.2-934.1] you apply the same weighted sum across all of the columns in this picture,

[t=934.0-938.3] producing a sequence of changes, adding all of those changes to the corresponding

[t=938.3-942.2] embeddings, produces a full sequence of more refined embeddings popping out

[t=942.2-943.5] of the attention block.

[t=944.9-949.1] Zooming out, this whole process is what you would describe as a single head of attention.

[t=949.6-954.2] As I've described things so far, this process is parameterized by three distinct

[t=954.2-958.9] matrices, all filled with tunable parameters, the key, the query, and the value.

[t=959.5-962.9] I want to take a moment to continue what we started in the last chapter,

[t=962.9-967.1] with the scorekeeping where we count up the total number of model parameters using the

[t=967.1-968.0] numbers from GPT-3.

[t=969.3-975.0] These key and query matrices each have 12,288 columns, matching the embedding dimension,

[t=975.0-979.6] and 128 rows, matching the dimension of that smaller key query space.

[t=980.3-984.2] This gives us an additional 1.5 million or so parameters for each one.

[t=984.9-990.1] If you look at that value matrix by contrast, the way I've described things so

[t=990.1-995.9] far would suggest that it's a square matrix that has 12,288 columns and 12,288 rows,

[t=995.9-1000.9] since both its inputs and outputs live in this very large embedding space.

[t=1001.5-1005.1] If true, that would mean about 150 million added parameters.

[t=1005.7-1007.3] And to be clear, you could do that.

[t=1007.4-1009.8] You could devote orders of magnitude more parameters

[t=1009.8-1011.7] to the value map than to the key and query.

[t=1012.1-1015.0] But in practice, it is much more efficient if instead you make

[t=1015.0-1017.9] it so that the number of parameters devoted to this value map

[t=1017.9-1020.8] is the same as the number devoted to the key and the query.

[t=1021.5-1023.3] This is especially relevant in the setting of

[t=1023.3-1025.2] running multiple attention heads in parallel.

[t=1026.2-1030.1] The way this looks is that the value map is factored as a product of two smaller matrices.

[t=1031.2-1035.3] Conceptually, I would still encourage you to think about the overall linear map,

[t=1035.3-1038.8] one with inputs and outputs, both in this larger embedding space,

[t=1038.8-1043.1] for example taking the embedding of blue to this blueness direction that you would

[t=1043.1-1043.8] add to nouns.

[t=1047.0-1050.3] The first matrix on the right here has a smaller number of rows,

[t=1050.3-1052.8] typically the same size as the key-query space

[t=1053.1-1055.7] What this means is you can think of it as mapping the

[t=1055.7-1058.4] large embedding vectors down to a much smaller space.

[t=1059.0-1062.7] This is not the conventional naming, but I'm going to call this the value down matrix.

[t=1063.4-1067.4] The second matrix maps from this smaller space back up to the embedding space,

[t=1067.4-1070.6] producing the vectors that you use to make the actual updates.

[t=1071.0-1074.7] I'm going to call this one the value up matrix, which again is not conventional.

[t=1075.2-1078.1] The way that you would see this written in most papers looks a little different.

[t=1078.4-1079.5] I'll talk about it in a minute.

[t=1079.7-1082.5] In my opinion, it tends to make things a little more conceptually confusing.

[t=1083.3-1086.8] To throw in linear algebra jargon here, what we're basically doing is

[t=1086.8-1090.3] constraining the overall value map to be a low rank transformation.

[t=1091.4-1096.1] Turning back to the parameter count, all four of these matrices have the same size,

[t=1096.1-1100.8] and adding them all up we get about 6.3 million parameters for one attention head.

[t=1102.0-1104.2] As a quick side note, to be a little more accurate,

[t=1104.2-1107.4] everything described so far is what people would call a self-attention head,

[t=1107.4-1110.5] to distinguish it from a variation that comes up in other models that's

[t=1110.5-1111.5] called cross-attention.

[t=1112.3-1115.7] This isn't relevant to our GPT example, but if you're curious,

[t=1115.7-1119.8] cross-attention involves models that process two distinct types of data,

[t=1119.8-1123.8] like text in one language and text in another language that's part of an

[t=1123.8-1128.0] ongoing generation of a translation, or maybe audio input of speech and an

[t=1128.0-1129.2] ongoing transcription.

[t=1130.4-1132.7] A cross-attention head looks almost identical.

[t=1133.0-1137.4] The only difference is that the key and query maps act on different data sets.

[t=1137.8-1142.1] In a model doing translation, for example, the keys might come from one language,

[t=1142.1-1146.1] while the queries come from another, and the attention pattern could describe

[t=1146.1-1149.7] which words from one language correspond to which words in another.

[t=1150.3-1152.9] And in this setting there would typically be no masking,

[t=1152.9-1156.3] since there's not really any notion of later tokens affecting earlier ones.

[t=1157.2-1160.8] Staying focused on self-attention though, if you understood everything so far,

[t=1160.8-1164.7] and if you were to stop here, you would come away with the essence of what attention

[t=1164.7-1165.2] really is.

[t=1165.8-1168.7] All that's really left to us is to lay out the sense

[t=1168.7-1171.4] in which you do this many many different times.

[t=1172.1-1175.1] In our central example we focused on adjectives updating nouns,

[t=1175.1-1178.9] but of course there are lots of different ways that context can influence the

[t=1178.9-1179.8] meaning of a word.

[t=1180.4-1183.2] If the words they crashed the preceded the word car,

[t=1183.2-1186.5] it has implications for the shape and structure of that car.

[t=1187.2-1189.3] And a lot of associations might be less grammatical.

[t=1189.8-1192.9] If the word wizard is anywhere in the same passage as Harry,

[t=1192.9-1195.9] it suggests that this might be referring to Harry Potter,

[t=1195.9-1200.0] whereas if instead the words Queen, Sussex, and William were in that passage,

[t=1200.0-1204.4] then perhaps the embedding of Harry should instead be updated to refer to the prince.

[t=1205.0-1208.5] For every different type of contextual updating that you might imagine,

[t=1208.5-1211.9] the parameters of these key and query matrices would be different to

[t=1211.9-1215.3] capture the different attention patterns, and the parameters of our

[t=1215.3-1219.1] value map would be different based on what should be added to the embeddings.

[t=1220.0-1223.1] And again, in practice the true behavior of these maps is much more

[t=1223.1-1226.3] difficult to interpret, where the weights are set to do whatever the

[t=1226.3-1230.1] model needs them to do to best accomplish its goal of predicting the next token.

[t=1231.4-1235.2] As I said before, everything we described is a single head of attention,

[t=1235.2-1238.7] and a full attention block inside a transformer consists of what's

[t=1238.7-1243.1] called multi-headed attention, where you run a lot of these operations in parallel,

[t=1243.1-1245.9] each with its own distinct key query and value maps.

[t=1247.4-1251.7] GPT-3 for example uses 96 attention heads inside each block.

[t=1252.0-1254.5] Considering that each one is already a bit confusing,

[t=1254.5-1256.5] it's certainly a lot to hold in your head.

[t=1256.8-1261.1] Just to spell it all out very explicitly, this means you have 96 distinct

[t=1261.1-1265.0] key and query matrices producing 96 distinct attention patterns.

[t=1265.4-1268.9] Then each head has its own distinct value matrices

[t=1268.9-1272.2] used to produce 96 sequences of value vectors.

[t=1272.5-1276.7] These are all added together using the corresponding attention patterns as weights.

[t=1277.5-1281.4] What this means is that for each position in the context, each token,

[t=1281.4-1286.2] every one of these heads produces a proposed change to be added to the embedding in

[t=1286.2-1287.0] that position.

[t=1287.7-1292.0] So what you do is you sum together all of those proposed changes, one for each head,

[t=1292.0-1295.5] and you add the result to the original embedding of that position.

[t=1296.7-1301.7] This entire sum here would be one slice of what's outputted from this multi-headed

[t=1301.7-1307.0] attention block, a single one of those refined embeddings that pops out the other end

[t=1307.0-1307.5] of it.

[t=1308.3-1310.2] Again, this is a lot to think about, so don't

[t=1310.2-1312.1] worry at all if it takes some time to sink in.

[t=1312.4-1316.3] The overall idea is that by running many distinct heads in parallel,

[t=1316.3-1320.8] you're giving the model the capacity to learn many distinct ways that context

[t=1320.8-1321.8] changes meaning.

[t=1323.7-1327.3] Pulling up our running tally for parameter count with 96 heads,

[t=1327.3-1330.5] each including its own variation of these four matrices,

[t=1330.5-1335.1] each block of multi-headed attention ends up with around 600 million parameters.

[t=1336.4-1339.0] There's one added slightly annoying thing that I should really

[t=1339.0-1341.8] mention for any of you who go on to read more about transformers.

[t=1342.1-1345.6] You remember how I said that the value map is factored out into these two

[t=1345.6-1349.4] distinct matrices, which I labeled as the value down and the value up matrices.

[t=1350.0-1354.2] The way that I framed things would suggest that you see this pair of matrices

[t=1354.2-1358.4] inside each attention head, and you could absolutely implement it this way.

[t=1358.6-1359.9] That would be a valid design.

[t=1360.3-1362.6] But the way that you see this written in papers and the way

[t=1362.6-1364.9] that it's implemented in practice looks a little different.

[t=1365.3-1370.8] All of these value up matrices for each head appear stapled together in one giant matrix

[t=1370.8-1376.4] that we call the output matrix, associated with the entire multi-headed attention block.

[t=1376.8-1380.6] And when you see people refer to the value matrix for a given attention head,

[t=1380.6-1383.2] they're typically only referring to this first step,

[t=1383.2-1387.1] the one that I was labeling as the value down projection into the smaller space.

[t=1388.3-1391.0] For the curious among you, I've left an on-screen note about it.

[t=1391.3-1393.6] It's one of those details that runs the risk of distracting

[t=1393.6-1396.0] from the main conceptual points, but I do want to call it out

[t=1396.0-1398.5] just so that you know if you read about this in other sources.

[t=1399.2-1403.7] Setting aside all the technical nuances, in the preview from the last chapter we saw how

[t=1403.7-1408.0] data flowing through a transformer doesn't just flow through a single attention block.

[t=1408.6-1412.7] For one thing, it also goes through these other operations called multi-layer perceptrons.

[t=1413.1-1414.9] We'll talk more about those in the next chapter.

[t=1415.2-1419.3] And then it repeatedly goes through many many copies of both of these operations.

[t=1420.0-1423.9] What this means is that after a given word imbibes some of its context,

[t=1423.9-1427.2] there are many more chances for this more nuanced embedding

[t=1427.2-1430.0] to be influenced by its more nuanced surroundings.

[t=1430.9-1434.9] The further down the network you go, with each embedding taking in more and more

[t=1434.9-1439.1] meaning from all the other embeddings, which themselves are getting more and more

[t=1439.1-1443.0] nuanced, the hope is that there's the capacity to encode higher level and more

[t=1443.0-1447.3] abstract ideas about a given input beyond just descriptors and grammatical structure.

[t=1447.9-1451.7] Things like sentiment and tone and whether it's a poem and what underlying

[t=1451.7-1455.1] scientific truths are relevant to the piece and things like that.

[t=1456.7-1462.0] Turning back one more time to our scorekeeping, GPT-3 includes 96 distinct layers,

[t=1462.0-1467.3] so the total number of key query and value parameters is multiplied by another 96,

[t=1467.3-1472.0] which brings the total sum to just under 58 billion distinct parameters

[t=1472.0-1474.5] devoted to all of the attention heads.

[t=1475.0-1478.0] That is a lot to be sure, but it's only about a third

[t=1478.0-1480.9] of the 175 billion that are in the network in total.

[t=1481.5-1484.1] So even though attention gets all of the attention,

[t=1484.1-1488.1] the majority of parameters come from the blocks sitting in between these steps.

[t=1488.6-1491.0] In the next chapter, you and I will talk more about those

[t=1491.0-1493.6] other blocks and also a lot more about the training process.

[t=1494.1-1498.8] A big part of the story for the success of the attention mechanism is not so much any

[t=1498.8-1503.0] specific kind of behaviour that it enables, but the fact that it's extremely

[t=1503.0-1507.7] parallelizable, meaning that you can run a huge number of computations in a short time

[t=1507.7-1508.4] using GPUs.

[t=1509.5-1513.3] Given that one of the big lessons about deep learning in the last decade or two has

[t=1513.3-1517.4] been that scale alone seems to give huge qualitative improvements in model performance,

[t=1517.4-1521.1] there's a huge advantage to parallelizable architectures that let you do this.

[t=1522.0-1525.3] If you want to learn more about this stuff, I've left lots of links in the description.

[t=1525.9-1530.0] In particular, anything produced by Andrej Karpathy or Chris Ola tend to be pure gold.

[t=1530.6-1533.7] In this video, I wanted to just jump into attention in its current form,

[t=1533.7-1536.7] but if you're curious about more of the history for how we got here

[t=1536.7-1538.9] and how you might reinvent this idea for yourself,

[t=1538.9-1542.5] my friend Vivek just put up a couple videos giving a lot more of that motivation.

[t=1543.1-1545.8] Also, Britt Cruz from the channel The Art of the Problem has a

[t=1545.8-1548.5] really nice video about the history of large language models.

[t=1565.0-1569.2] Thank you.
