---
schema_version: 1
id: note_source_youtube_video_wjzofjx0v4m_e014c73c
subjects:
  - attn
related_los: []
related_concepts: []
source_type: canonical_source
canonical_source:
  kind: youtube_video
  original_uri: https://www.youtube.com/watch?v=wjZofJX0v4M
  canonical_uri: https://www.youtube.com/watch?v=wjZofJX0v4M
  title: YouTube video wjZofJX0v4M
  authors: []
  retrieved_at: '2026-05-28T20:35:23Z'
  content_hash: 
    sha256:e014c73c8becc5619403837ef486e5f52ed2f9ee1766eb90004731483f6c0602
  license_hint:
created_at: '2026-05-28T20:35:23Z'
updated_at: '2026-05-28T20:35:23Z'
---

# YouTube video wjZofJX0v4M

[t=0.0-4.6] The initials GPT stand for Generative Pretrained Transformer.

[t=5.2-9.0] So that first word is straightforward enough, these are bots that generate new text.

[t=9.8-13.2] Pretrained refers to how the model went through a process of learning

[t=13.2-16.6] from a massive amount of data, and the prefix insinuates that there's

[t=16.6-20.0] more room to fine-tune it on specific tasks with additional training.

[t=20.7-22.9] But the last word, that's the real key piece.

[t=23.4-27.6] A transformer is a specific kind of neural network, a machine learning model,

[t=27.6-31.0] and it's the core invention underlying the current boom in AI.

[t=31.7-35.4] What I want to do with this video and the following chapters is go through a

[t=35.4-39.1] visually-driven explanation for what actually happens inside a transformer.

[t=39.7-42.8] We're going to follow the data that flows through it and go step by step.

[t=43.4-47.4] There are many different kinds of models that you can build using transformers.

[t=47.8-50.8] Some models take in audio and produce a transcript.

[t=51.3-54.2] This sentence comes from a model going the other way around,

[t=54.2-56.2] producing synthetic speech just from text.

[t=56.7-61.1] All those tools that took the world by storm in 2022 like DALL-E and Midjourney

[t=61.1-65.5] that take in a text description and produce an image are based on transformers.

[t=66.0-69.7] Even if I can't quite get it to understand what a pi creature is supposed to be,

[t=69.7-73.1] I'm still blown away that this kind of thing is even remotely possible.

[t=73.9-78.0] And the original transformer introduced in 2017 by Google was invented for

[t=78.0-82.1] the specific use case of translating text from one language into another.

[t=82.7-86.4] But the variant that you and I will focus on, which is the type that

[t=86.4-91.3] underlies tools like ChatGPT, will be a model that's trained to take in a piece of text,

[t=91.3-94.9] maybe even with some surrounding images or sound accompanying it,

[t=94.9-98.3] and produce a prediction for what comes next in the passage.

[t=98.6-101.3] That prediction takes the form of a probability distribution

[t=101.3-103.8] over many different chunks of text that might follow.

[t=105.0-107.6] At first glance, you might think that predicting the next word

[t=107.6-109.9] feels like a very different goal from generating new text.

[t=110.2-112.5] But once you have a prediction model like this,

[t=112.5-116.2] a simple thing you could try to make it generate, a longer piece of text,

[t=116.2-118.5] is to give it an initial snippet to work with,

[t=118.5-122.0] have it take a random sample from the distribution it just generated,

[t=122.0-125.9] append that sample to the text, and then run the whole process again to make

[t=125.9-129.5] a new prediction based on all the new text, including what it just added.

[t=130.1-133.0] I don't know about you, but it really doesn't feel like this should actually work.

[t=133.4-137.9] In this animation, for example, I'm running GPT-2 on my laptop and having it repeatedly

[t=137.9-142.4] predict and sample the next chunk of text to generate a story based on the seed text.

[t=142.4-146.1] The story just doesn't actually really make that much sense.

[t=146.5-151.3] But if I swap it out for API calls to GPT-3 instead, which is the same basic model,

[t=151.3-155.5] just much bigger, suddenly almost magically we do get a sensible story,

[t=155.5-160.1] one that even seems to infer that a pi creature would live in a land of math and

[t=160.1-160.9] computation.

[t=161.6-164.9] This process here of repeated prediction and sampling is essentially

[t=164.9-167.3] what's happening when you interact with ChatGPT,

[t=167.3-170.9] or any of these other large language models, and you see them producing

[t=170.9-171.9] one word at a time.

[t=172.5-175.8] In fact, one feature that I would very much enjoy is the ability to

[t=175.8-179.2] see the underlying distribution for each new word that it chooses.

[t=183.8-186.3] Let's kick things off with a very high level preview

[t=186.3-188.2] of how data flows through a transformer.

[t=188.6-192.0] We will spend much more time motivating and interpreting and expanding

[t=192.0-194.4] on the details of each step, but in broad strokes,

[t=194.4-198.7] when one of these chatbots generates a given word, here's what's going on under the hood.

[t=199.1-202.0] First, the input is broken up into a bunch of little pieces.

[t=202.6-206.2] These pieces are called tokens, and in the case of text these tend to be

[t=206.2-209.8] words or little pieces of words or other common character combinations.

[t=210.7-214.1] If images or sound are involved, then tokens could be little

[t=214.1-217.1] patches of that image or little chunks of that sound.

[t=217.6-222.2] Each one of these tokens is then associated with a vector, meaning some list of numbers,

[t=222.2-225.4] which is meant to somehow encode the meaning of that piece.

[t=225.9-230.1] If you think of these vectors as giving coordinates in some very high dimensional space,

[t=230.1-233.0] words with similar meanings tend to land on vectors that are

[t=233.0-234.7] close to each other in that space.

[t=235.3-238.2] This sequence of vectors then passes through an operation that's

[t=238.2-241.3] known as an attention block, and this allows the vectors to talk to

[t=241.3-244.5] each other and pass information back and forth to update their values.

[t=244.9-248.5] For example, the meaning of the word model in the phrase "a machine learning

[t=248.5-251.8] model" is different from its meaning in the phrase "a fashion model".

[t=252.3-255.5] The attention block is what's responsible for figuring out which

[t=255.5-259.4] words in context are relevant to updating the meanings of which other words,

[t=259.4-262.0] and how exactly those meanings should be updated.

[t=262.5-265.1] And again, whenever I use the word meaning, this is

[t=265.1-268.0] somehow entirely encoded in the entries of those vectors.

[t=269.2-272.3] After that, these vectors pass through a different kind of operation,

[t=272.3-275.4] and depending on the source that you're reading this will be referred

[t=275.4-278.2] to as a multi-layer perceptron or maybe a feed-forward layer.

[t=278.6-280.5] And here the vectors don't talk to each other,

[t=280.5-282.7] they all go through the same operation in parallel.

[t=283.1-285.7] And while this block is a little bit harder to interpret,

[t=285.7-289.5] later on we'll talk about how the step is a little bit like asking a long list

[t=289.5-293.1] of questions about each vector, and then updating them based on the answers

[t=293.1-294.0] to those questions.

[t=294.9-298.2] All of the operations in both of these blocks look like a

[t=298.2-301.7] giant pile of matrix multiplications, and our primary job is

[t=301.7-305.3] going to be to understand how to read the underlying matrices.

[t=307.0-310.9] I'm glossing over some details about some normalization steps that happen in between,

[t=310.9-313.0] but this is after all a high-level preview.

[t=313.7-317.2] After that, the process essentially repeats, you go back and forth

[t=317.2-320.5] between attention blocks and multi-layer perceptron blocks,

[t=320.5-324.1] until at the very end the hope is that all of the essential meaning

[t=324.1-328.5] of the passage has somehow been baked into the very last vector in the sequence.

[t=328.9-333.3] We then perform a certain operation on that last vector that produces a probability

[t=333.3-337.8] distribution over all possible tokens, all possible little chunks of text that might

[t=337.8-338.4] come next.

[t=339.0-342.3] And like I said, once you have a tool that predicts what comes next

[t=342.3-345.9] given a snippet of text, you can feed it a little bit of seed text and

[t=345.9-349.1] have it repeatedly play this game of predicting what comes next,

[t=349.1-353.1] sampling from the distribution, appending it, and then repeating over and over.

[t=353.6-357.9] Some of you in the know may remember how long before ChatGPT came into the scene,

[t=357.9-360.4] this is what early demos of GPT-3 looked like,

[t=360.4-364.6] you would have it autocomplete stories and essays based on an initial snippet.

[t=365.6-369.8] To make a tool like this into a chatbot, the easiest starting point is to have a

[t=369.8-373.9] little bit of text that establishes the setting of a user interacting with a

[t=373.9-377.1] helpful AI assistant, what you would call the system prompt,

[t=377.1-381.4] and then you would use the user's initial question or prompt as the first bit of

[t=381.4-385.7] dialogue, and then you have it start predicting what such a helpful AI assistant

[t=385.7-386.9] would say in response.

[t=387.7-391.0] There is more to say about an added step of training that's required

[t=391.0-393.9] to make this work well, but at a high level this is the idea.

[t=395.7-400.0] In this chapter, you and I are going to expand on the details of what happens at the very

[t=400.0-402.7] beginning of the network, at the very end of the network,

[t=402.7-406.7] and I also want to spend a lot of time reviewing some important bits of background

[t=406.7-410.9] knowledge, things that would have been second nature to any machine learning engineer by

[t=410.9-412.6] the time transformers came around.

[t=413.1-416.2] If you're comfortable with that background knowledge and a little impatient,

[t=416.2-418.6] you could probably feel free to skip to the next chapter,

[t=418.6-420.7] which is going to focus on the attention blocks,

[t=420.7-422.8] generally considered the heart of the transformer.

[t=423.4-427.0] After that, I want to talk more about these multi-layer perceptron blocks,

[t=427.0-431.1] how training works, and a number of other details that will have been skipped up to

[t=431.1-431.7] that point.

[t=432.2-436.2] For broader context, these videos are additions to a mini-series about deep learning,

[t=436.2-438.9] and it's okay if you haven't watched the previous ones,

[t=438.9-442.9] I think you can do it out of order, but before diving into transformers specifically,

[t=442.9-447.0] I do think it's worth making sure that we're on the same page about the basic premise

[t=447.0-448.5] and structure of deep learning.

[t=449.0-453.2] At the risk of stating the obvious, this is one approach to machine learning,

[t=453.2-457.8] which describes any model where you're using data to somehow determine how a model

[t=457.8-458.3] behaves.

[t=459.1-462.5] What I mean by that is, let's say you want a function that takes in

[t=462.5-464.9] an image and it produces a label describing it,

[t=464.9-468.2] or our example of predicting the next word given a passage of text,

[t=468.2-471.5] or any other task that seems to require some element of intuition

[t=471.5-472.8] and pattern recognition.

[t=473.2-477.7] We almost take this for granted these days, but the idea with machine learning is that

[t=477.7-482.1] rather than trying to explicitly define a procedure for how to do that task in code,

[t=482.1-485.5] which is what people would have done in the earliest days of AI,

[t=485.5-489.2] instead you set up a very flexible structure with tunable parameters,

[t=489.2-491.9] like a bunch of knobs and dials, and then, somehow,

[t=491.9-496.4] you use many examples of what the output should look like for a given input to tweak

[t=496.4-499.7] and tune the values of those parameters to mimic this behavior.

[t=499.7-504.1] For example, maybe the simplest form of machine learning is linear regression,

[t=504.1-507.2] where your inputs and outputs are each single numbers,

[t=507.2-510.6] something like the square footage of a house and its price,

[t=510.6-515.0] and what you want is to find a line of best fit through this data, you know,

[t=515.0-516.8] to predict future house prices.

[t=517.4-520.5] That line is described by two continuous parameters,

[t=520.5-524.0] say the slope and the y-intercept, and the goal of linear

[t=524.0-528.2] regression is to determine those parameters to closely match the data.

[t=528.9-532.1] Needless to say, deep learning models get much more complicated.

[t=532.6-537.7] GPT-3, for example, has not two, but 175 billion parameters.

[t=538.1-542.0] But here's the thing, it's not a given that you can create some giant

[t=542.0-545.6] model with a huge number of parameters without it either grossly

[t=545.6-549.6] overfitting the training data or being completely intractable to train.

[t=550.3-553.1] Deep learning describes a class of models that in the

[t=553.1-556.2] last couple decades have proven to scale remarkably well.

[t=556.5-559.7] What unifies them is that they all use the same training algorithm,

[t=559.7-563.0] it's called backpropagation, we talked about it in previous chapters,

[t=563.0-566.7] and the context that I want you to have as we go in is that in order for this

[t=566.7-570.5] training algorithm to work well at scale, these models have to follow a certain

[t=570.5-571.3] specific format.

[t=571.8-576.1] And if you know this format going in, it helps to explain many of the choices for how a

[t=576.1-580.4] transformer processes language, which otherwise run the risk of feeling kinda arbitrary.

[t=581.4-583.9] First, whatever kind of model you're making, the

[t=583.9-586.7] input has to be formatted as an array of real numbers.

[t=586.7-590.9] This could simply mean a list of numbers, it could be a two-dimensional array,

[t=590.9-593.9] or very often you deal with higher dimensional arrays,

[t=593.9-596.0] where the general term used is tensor.

[t=596.6-600.5] You often think of that input data as being progressively transformed into many

[t=600.5-604.4] distinct layers, where again, each layer is always structured as some kind of

[t=604.4-608.7] array of real numbers, until you get to a final layer which you consider the output.

[t=609.3-613.3] For example, the final layer in our text processing model is a list of numbers

[t=613.3-617.1] representing the probability distribution for all possible next tokens.

[t=617.8-622.0] In deep learning, these model parameters are almost always referred to as weights,

[t=622.0-626.0] and this is because a key feature of these models is that the only way these

[t=626.0-629.9] parameters interact with the data being processed is through weighted sums.

[t=630.3-632.7] You also sprinkle some non-linear functions throughout,

[t=632.7-634.4] but they won't depend on parameters.

[t=635.2-638.6] Typically, though, instead of seeing the weighted sums all naked

[t=638.6-642.0] and written out explicitly like this, you'll instead find them

[t=642.0-645.6] packaged together as various components in a matrix vector product.

[t=646.7-650.4] It amounts to saying the same thing, if you think back to how matrix vector

[t=650.4-654.2] multiplication works, each component in the output looks like a weighted sum.

[t=654.8-658.2] It's just often conceptually cleaner for you and me to think

[t=658.2-661.7] about matrices that are filled with tunable parameters that

[t=661.7-665.4] transform vectors that are drawn from the data being processed.

[t=666.3-670.2] For example, those 175 billion weights in GPT-3 are

[t=670.2-674.2] organized into just under 28,000 distinct matrices.

[t=674.7-677.4] Those matrices in turn fall into eight different categories,

[t=677.4-681.2] and what you and I are going to do is step through each one of those categories to

[t=681.2-682.7] understand what that type does.

[t=683.2-687.1] As we go through, I think it's kind of fun to reference the specific

[t=687.1-691.4] numbers from GPT-3 to count up exactly where those 175 billion come from.

[t=691.9-694.4] Even if nowadays there are bigger and better models,

[t=694.4-697.2] this one has a certain charm as the first large-language

[t=697.2-700.7] model to really capture the world's attention outside of ML communities.

[t=701.4-704.2] Also, practically speaking, companies tend to keep much tighter

[t=704.2-706.7] lips around the specific numbers for more modern networks.

[t=707.4-710.7] I just want to set the scene going in, that as you peek under the

[t=710.7-713.4] hood to see what happens inside a tool like ChatGPT,

[t=713.4-717.4] almost all of the actual computation looks like matrix vector multiplication.

[t=717.9-721.9] There's a little bit of a risk getting lost in the sea of billions of numbers,

[t=721.9-725.3] but you should draw a very sharp distinction in your mind between

[t=725.3-728.6] the weights of the model, which I'll always color in blue or red,

[t=728.6-731.8] and the data being processed, which I'll always color in gray.

[t=732.2-736.2] The weights are the actual brains, they are the things learned during training,

[t=736.2-737.9] and they determine how it behaves.

[t=738.3-742.3] The data being processed simply encodes whatever specific input is

[t=742.3-746.5] fed into the model for a given run, like an example snippet of text.

[t=747.5-751.7] With all of that as foundation, let's dig into the first step of this text processing

[t=751.7-756.0] example, which is to break up the input into little chunks and turn those chunks into

[t=756.0-756.4] vectors.

[t=757.0-759.3] I mentioned how those chunks are called tokens,

[t=759.3-761.5] which might be pieces of words or punctuation,

[t=761.5-764.9] but every now and then in this chapter and especially in the next one,

[t=764.9-768.1] I'd like to just pretend that it's broken more cleanly into words.

[t=768.6-771.4] Because we humans think in words, this will just make it much

[t=771.4-774.1] easier to reference little examples and clarify each step.

[t=775.3-779.4] The model has a predefined vocabulary, some list of all possible words,

[t=779.4-783.1] say 50,000 of them, and the first matrix that we'll encounter,

[t=783.1-787.8] known as the embedding matrix, has a single column for each one of these words.

[t=788.9-793.8] These columns are what determines what vector each word turns into in that first step.

[t=795.1-798.1] We label it W_E, and like all the matrices we see,

[t=798.1-802.4] its values begin random, but they're going to be learned based on data.

[t=803.6-807.4] Turning words into vectors was common practice in machine learning long before

[t=807.4-810.8] transformers, but it's a little weird if you've never seen it before,

[t=810.8-813.4] and it sets the foundation for everything that follows,

[t=813.4-815.8] so let's take a moment to get familiar with it.

[t=816.0-819.9] We often call this embedding a word, which invites you to think of these

[t=819.9-823.6] vectors very geometrically as points in some high dimensional space.

[t=824.2-828.1] Visualizing a list of three numbers as coordinates for points in 3D space would

[t=828.1-831.8] be no problem, but word embeddings tend to be much much higher dimensional.

[t=832.3-835.9] In GPT-3 they have 12,288 dimensions, and as you'll see,

[t=835.9-840.4] it matters to work in a space that has a lot of distinct directions.

[t=841.2-845.1] In the same way that you could take a two-dimensional slice through a 3D space

[t=845.1-848.8] and project all the points onto that slice, for the sake of animating word

[t=848.8-852.5] embeddings that a simple model is giving me, I'm going to do an analogous

[t=852.5-856.7] thing by choosing a three-dimensional slice through this very high dimensional space,

[t=856.7-860.5] and projecting the word vectors down onto that and displaying the results.

[t=861.3-865.5] The big idea here is that as a model tweaks and tunes its weights to determine

[t=865.5-868.7] how exactly words get embedded as vectors during training,

[t=868.7-873.0] it tends to settle on a set of embeddings where directions in the space have a

[t=873.0-874.4] kind of semantic meaning.

[t=875.0-877.8] For the simple word-to-vector model I'm running here,

[t=877.8-882.2] if I run a search for all the words whose embeddings are closest to that of tower,

[t=882.2-885.9] you'll notice how they all seem to give very similar tower-ish vibes.

[t=886.3-888.8] And if you want to pull up some Python and play along at home,

[t=888.8-891.4] this is the specific model that I'm using to make the animations.

[t=891.6-894.5] It's not a transformer, but it's enough to illustrate the

[t=894.5-897.6] idea that directions in the space can carry semantic meaning.

[t=898.3-902.2] A very classic example of this is how if you take the difference between

[t=902.2-905.8] the vectors for woman and man, something you would visualize as a

[t=905.8-910.0] little vector in the space connecting the tip of one to the tip of the other,

[t=910.0-913.2] it's very similar to the difference between king and queen.

[t=915.1-918.4] So let's say you didn't know the word for a female monarch,

[t=918.4-922.4] you could find it by taking king, adding this woman minus man direction,

[t=922.4-925.5] and searching for the embedding closest to that point.

[t=927.0-928.2] At least, kind of.

[t=928.5-931.8] Despite this being a classic example for the model I'm playing with,

[t=931.8-935.9] the true embedding of queen is actually a little farther off than this would suggest,

[t=935.9-940.0] presumably because the way queen is used in training data is not merely a feminine

[t=940.0-940.8] version of king.

[t=941.6-945.3] When I played around, family relations seemed to illustrate the idea much better.

[t=946.3-950.5] The point is, it looks like during training the model found it advantageous to

[t=950.5-954.9] choose embeddings such that one direction in this space encodes gender information.

[t=956.8-960.1] Another example is that if you take the embedding of Italy,

[t=960.1-964.8] and you subtract the embedding of Germany, and add that to the embedding of Hitler,

[t=964.8-968.1] you get something very close to the embedding of Mussolini.

[t=968.6-973.4] It's as if the model learned to associate some directions with Italian-ness,

[t=973.4-975.7] and others with WWII axis leaders.

[t=976.5-979.9] Maybe my favorite example in this vein is how in some models,

[t=979.9-984.2] if you take the difference between Germany and Japan, and add it to sushi,

[t=984.2-986.2] you end up very close to bratwurst.

[t=987.4-990.2] Also in playing this game of finding nearest neighbors,

[t=990.2-993.9] I was very pleased to see how close cat was to both beast and monster.

[t=994.7-997.7] One bit of mathematical intuition that's helpful to have in mind,

[t=997.7-1000.7] especially for the next chapter, is how the dot product of two

[t=1000.7-1003.9] vectors can be thought of as a way to measure how well they align.

[t=1004.9-1007.7] Computationally, dot products involve multiplying all the

[t=1007.7-1011.1] corresponding components and then adding the results, which is good,

[t=1011.1-1014.3] since so much of our computation has to look like weighted sums.

[t=1015.2-1020.0] Geometrically, the dot product is positive when vectors point in similar directions,

[t=1020.0-1023.6] it's zero if they're perpendicular, and it's negative whenever

[t=1023.6-1025.6] they point in opposite directions.

[t=1026.5-1029.9] For example, let's say you were playing with this model,

[t=1029.9-1034.9] and you hypothesize that the embedding of cats minus cat might represent a sort of

[t=1034.9-1037.0] plurality direction in this space.

[t=1037.4-1040.6] To test this, I'm going to take this vector and compute its dot

[t=1040.6-1043.5] product against the embeddings of certain singular nouns,

[t=1043.5-1047.0] and compare it to the dot products with the corresponding plural nouns.

[t=1047.3-1050.2] If you play around with this, you'll notice that the plural ones

[t=1050.2-1053.6] do indeed seem to consistently give higher values than the singular ones,

[t=1053.6-1056.1] indicating that they align more with this direction.

[t=1057.1-1061.6] It's also fun how if you take this dot product with the embeddings of the words one,

[t=1061.6-1064.4] two, three, and so on, they give increasing values,

[t=1064.4-1069.0] so it's as if we can quantitatively measure how plural the model finds a given word.

[t=1070.2-1073.6] Again, the specifics for how words get embedded is learned using data.

[t=1074.0-1077.5] This embedding matrix, whose columns tell us what happens to each word,

[t=1077.5-1079.5] is the first pile of weights in our model.

[t=1080.0-1084.7] Using the GPT-3 numbers, the vocabulary size specifically is 50,257,

[t=1084.7-1089.8] and again, technically this consists not of words per se, but of tokens.

[t=1090.6-1094.3] The embedding dimension is 12,288, and multiplying those

[t=1094.3-1097.8] tells us this consists of about 617 million weights.

[t=1098.2-1100.6] Let's go ahead and add this to a running tally,

[t=1100.6-1103.8] remembering that by the end we should count up to 175 billion.

[t=1105.4-1108.8] In the case of transformers, you really want to think of the vectors

[t=1108.8-1112.1] in this embedding space as not merely representing individual words.

[t=1112.5-1116.5] For one thing, they also encode information about the position of that word,

[t=1116.5-1119.2] which we'll talk about later, but more importantly,

[t=1119.2-1122.8] you should think of them as having the capacity to soak in context.

[t=1123.3-1127.4] A vector that started its life as the embedding of the word king, for example,

[t=1127.4-1131.4] might progressively get tugged and pulled by various blocks in this network,

[t=1131.4-1135.6] so that by the end it points in a much more specific and nuanced direction that

[t=1135.6-1138.6] somehow encodes that it was a king who lived in Scotland,

[t=1138.6-1142.0] and who had achieved his post after murdering the previous king,

[t=1142.0-1144.7] and who's being described in Shakespearean language.

[t=1145.2-1147.8] Think about your own understanding of a given word.

[t=1148.2-1151.7] The meaning of that word is clearly informed by the surroundings,

[t=1151.7-1155.1] and sometimes this includes context from a long distance away,

[t=1155.1-1159.6] so in putting together a model that has the ability to predict what word comes next,

[t=1159.6-1163.4] the goal is to somehow empower it to incorporate context efficiently.

[t=1164.0-1167.1] To be clear, in that very first step, when you create the array of

[t=1167.1-1170.4] vectors based on the input text, each one of those is simply plucked

[t=1170.4-1173.5] out of the embedding matrix, so initially each one can only encode

[t=1173.5-1176.8] the meaning of a single word without any input from its surroundings.

[t=1177.7-1181.6] But you should think of the primary goal of this network that it flows through

[t=1181.6-1185.4] as being to enable each one of those vectors to soak up a meaning that's much

[t=1185.4-1189.0] more rich and specific than what mere individual words could represent.

[t=1189.5-1192.8] The network can only process a fixed number of vectors at a time,

[t=1192.8-1194.2] known as its context size.

[t=1194.5-1197.7] For GPT-3 it was trained with a context size of 2048,

[t=1197.7-1202.8] so the data flowing through the network always looks like this array of 2048 columns,

[t=1202.8-1205.0] each of which has 12,000 dimensions.

[t=1205.6-1208.7] This context size limits how much text the transformer can

[t=1208.7-1211.8] incorporate when it's making a prediction of the next word.

[t=1212.4-1215.0] This is why long conversations with certain chatbots,

[t=1215.0-1218.2] like the early versions of ChatGPT, often gave the feeling of

[t=1218.2-1222.0] the bot kind of losing the thread of conversation as you continued too long.

[t=1223.0-1225.2] We'll go into the details of attention in due time,

[t=1225.2-1228.8] but skipping ahead I want to talk for a minute about what happens at the very end.

[t=1229.5-1232.0] Remember, the desired output is a probability

[t=1232.0-1234.9] distribution over all tokens that might come next.

[t=1235.2-1237.8] For example, if the very last word is Professor,

[t=1237.8-1240.5] and the context includes words like Harry Potter,

[t=1240.5-1243.5] and immediately preceding we see least favorite teacher,

[t=1243.5-1247.7] and also if you give me some leeway by letting me pretend that tokens simply

[t=1247.7-1251.9] look like full words, then a well-trained network that had built up knowledge

[t=1251.9-1255.8] of Harry Potter would presumably assign a high number to the word Snape.

[t=1256.5-1258.0] This involves two different steps.

[t=1258.3-1263.1] The first one is to use another matrix that maps the very last vector in that

[t=1263.1-1267.6] context to a list of 50,000 values, one for each token in the vocabulary.

[t=1268.2-1272.2] Then there's a function that normalizes this into a probability distribution,

[t=1272.2-1275.7] it's called softmax and we'll talk more about it in just a second,

[t=1275.7-1279.9] but before that it might seem a little bit weird to only use this last embedding

[t=1279.9-1283.9] to make a prediction, when after all in that last step there are thousands of

[t=1283.9-1288.3] other vectors in the layer just sitting there with their own context-rich meanings.

[t=1288.9-1292.7] This has to do with the fact that in the training process it turns out to be

[t=1292.7-1296.4] much more efficient if you use each one of those vectors in the final layer

[t=1296.4-1300.3] to simultaneously make a prediction for what would come immediately after it.

[t=1301.0-1303.2] There's a lot more to be said about training later on,

[t=1303.2-1305.1] but I just want to call that out right now.

[t=1305.7-1309.7] This matrix is called the Unembedding matrix and we give it the label WU.

[t=1310.2-1313.6] Again, like all the weight matrices we see, its entries begin at random,

[t=1313.6-1315.9] but they are learned during the training process.

[t=1316.5-1319.4] Keeping score on our total parameter count, this Unembedding

[t=1319.4-1322.0] matrix has one row for each word in the vocabulary,

[t=1322.0-1325.7] and each row has the same number of elements as the embedding dimension.

[t=1326.4-1330.4] It's very similar to the embedding matrix, just with the order swapped,

[t=1330.4-1333.6] so it adds another 617 million parameters to the network,

[t=1333.6-1336.6] meaning our count so far is a little over a billion,

[t=1336.6-1340.2] a small but not wholly insignificant fraction of the 175 billion

[t=1340.2-1341.8] we'll end up with in total.

[t=1342.5-1344.7] As the very last mini-lesson for this chapter,

[t=1344.7-1346.9] I want to talk more about this softmax function,

[t=1346.9-1350.6] since it makes another appearance for us once we dive into the attention blocks.

[t=1351.4-1356.6] The idea is that if you want a sequence of numbers to act as a probability distribution,

[t=1356.6-1359.4] say a distribution over all possible next words,

[t=1359.4-1364.6] then each value has to be between 0 and 1, and you also need all of them to add up to 1.

[t=1365.2-1369.9] However, if you're playing the deep learning game where everything you do looks like

[t=1369.9-1374.8] matrix-vector multiplication, the outputs you get by default don't abide by this at all.

[t=1375.3-1377.8] The values are often negative, or much bigger than 1,

[t=1377.8-1379.9] and they almost certainly don't add up to 1.

[t=1380.5-1384.0] Softmax is the standard way to turn an arbitrary list of numbers

[t=1384.0-1388.7] into a valid distribution in such a way that the largest values end up closest to 1,

[t=1388.7-1391.3] and the smaller values end up very close to 0.

[t=1391.8-1393.1] That's all you really need to know.

[t=1393.1-1397.1] But if you're curious, the way it works is to first raise e to the power

[t=1397.1-1401.4] of each of the numbers, which means you now have a list of positive values,

[t=1401.4-1405.6] and then you can take the sum of all those positive values and divide each

[t=1405.6-1409.5] term by that sum, which normalizes it into a list that adds up to 1.

[t=1410.2-1414.3] You'll notice that if one of the numbers in the input is meaningfully bigger than the

[t=1414.3-1418.0] rest, then in the output the corresponding term dominates the distribution,

[t=1418.0-1422.1] so if you were sampling from it you'd almost certainly just be picking the maximizing

[t=1422.1-1422.5] input.

[t=1423.0-1427.0] But it's softer than just picking the max in the sense that when other values

[t=1427.0-1430.9] are similarly large, they also get meaningful weight in the distribution,

[t=1430.8-1434.6] and everything changes continuously as you continuously vary the inputs.

[t=1435.1-1440.0] In some situations, like when ChatGPT is using this distribution to create a next word,

[t=1440.0-1444.7] there's room for a little bit of extra fun by adding a little extra spice into this

[t=1444.7-1448.9] function, with a constant T thrown into the denominator of those exponents.

[t=1449.5-1454.0] We call it the temperature, since it vaguely resembles the role of temperature in

[t=1454.0-1458.1] certain thermodynamics equations, and the effect is that when T is larger,

[t=1458.1-1462.7] you give more weight to the lower values, meaning the distribution is a little bit

[t=1462.7-1466.9] more uniform, and if T is smaller, then the bigger values will dominate more

[t=1466.9-1471.5] aggressively, where in the extreme, setting T equal to zero means all of the weight

[t=1471.5-1472.8] goes to maximum value.

[t=1473.5-1477.7] For example, I'll have GPT-3 generate a story with the seed text,

[t=1477.7-1483.0] "once upon a time there was A", but I'll use different temperatures in each case.

[t=1483.6-1488.3] Temperature zero means that it always goes with the most predictable word,

[t=1488.3-1492.4] and what you get ends up being a trite derivative of Goldilocks.

[t=1493.0-1496.5] A higher temperature gives it a chance to choose less likely words,

[t=1496.5-1497.9] but it comes with a risk.

[t=1498.2-1501.1] In this case, the story starts out more originally,

[t=1501.1-1506.0] about a young web artist from South Korea, but it quickly degenerates into nonsense.

[t=1507.0-1510.8] Technically speaking, the API doesn't actually let you pick a temperature bigger than 2.

[t=1511.2-1515.3] There's no mathematical reason for this, it's just an arbitrary constraint imposed

[t=1515.3-1519.3] to keep their tool from being seen generating things that are too nonsensical.

[t=1519.9-1524.3] So if you're curious, the way this animation is actually working is I'm taking the

[t=1524.3-1527.0] 20 most probable next tokens that GPT-3 generates,

[t=1527.0-1529.5] which seems to be the maximum they'll give me,

[t=1529.5-1533.0] and then I tweak the probabilities based on an exponent of 1/5.

[t=1533.1-1537.4] As another bit of jargon, in the same way that you might call the components of

[t=1537.4-1542.2] the output of this function probabilities, people often refer to the inputs as logits,

[t=1542.2-1546.2] or some people say logits, some people say logits, I'm gonna say logits.

[t=1546.5-1550.4] So for instance, when you feed in some text, you have all these word embeddings

[t=1550.4-1554.0] flow through the network, and you do this final multiplication with the

[t=1554.0-1558.2] unembedding matrix, machine learning people would refer to the components in that raw,

[t=1558.2-1561.4] unnormalized output as the logits for the next word prediction.

[t=1563.3-1566.7] A lot of the goal with this chapter was to lay the foundations for

[t=1566.7-1570.4] understanding the attention mechanism, Karate Kid wax-on-wax-off style.

[t=1570.8-1574.9] You see, if you have a strong intuition for word embeddings, for softmax,

[t=1574.9-1579.2] for how dot products measure similarity, and also the underlying premise that

[t=1579.2-1583.6] most of the calculations have to look like matrix multiplication with matrices

[t=1583.6-1587.6] full of tunable parameters, then understanding the attention mechanism,

[t=1587.6-1592.2] this cornerstone piece in the whole modern boom in AI, should be relatively smooth.

[t=1592.7-1594.5] For that, come join me in the next chapter.

[t=1596.4-1598.9] As I'm publishing this, a draft of that next chapter

[t=1598.9-1601.2] is available for review by Patreon supporters.

[t=1601.8-1604.2] A final version should be up in public in a week or two,

[t=1604.2-1607.4] it usually depends on how much I end up changing based on that review.

[t=1607.8-1609.7] In the meantime, if you want to dive into attention,

[t=1609.7-1612.4] and if you want to help the channel out a little bit, it's there waiting.
