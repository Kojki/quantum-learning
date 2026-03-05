# Step 02：ディラック記法とベクトル表記について
---

## このステップで学ぶこと
- 量子状態のディラック記法を用いた表し方
- テンソル積とは？
- 複数の量子状態の表し方

---

## 注意書き
この先は線形数学の基本的な知識があるとスムーズに理解ができます。
行列・ベクトルについて、ネット上でいいので簡単に調べておくことをお勧めします。

## 基本的な量子状態の表し方
量子状態における0と1は、数学的には $$|0\rangle, |1\rangle$$ と表記します。これらはそれぞれ

$$\begin{pmatrix}
1 \\
0
\end{pmatrix}, \begin{pmatrix}
0 \\
1
\end{pmatrix}$$

に相当するものです。
また、重ね合わせ状態も２通りあり、それぞれ $$|+\rangle, |-\rangle$$ と表記します。ベクトル表記は次の通りです。

$$
\frac{1}{\sqrt{2}}
\begin{pmatrix}
1 \\
1
\end{pmatrix} , \frac{1}{\sqrt{2}}
\begin{pmatrix}
1 \\
-1
\end{pmatrix}
$$

量子技術を用いて何かをするときにはこういったものがよく出てくるので、今のうちに慣れておいてください。細かい部分や計算のあたりは後ほど触れていきます。

## ディラック記法について

別名ブラケット記法ともいいますが、$|$ と $>$ などを用いて表すものをディラック記法といいます。
先ほど|0>のようなものが出てきましたが、これは「ケット」と呼ばれるものです。こういったものとは別に<0|や<1|というものがあります。これは「ブラ」と呼ばれます。
「ブラ」は「ケット」のエルミート共役（転置をして複素共役をとったもの）に対応していて具体的には、
$\langle 0 | = \begin{pmatrix} 1 & 0 \end{pmatrix}$ $\langle 1 | = \begin{pmatrix} 0 & 1 \end{pmatrix}$
のようになります。

ディラック記法は、内積や行列を表す際にも非常に便利なのでよく使われます。

例えば内積であれば、
$$\langle 0 | 0 \rangle =  
\begin{pmatrix} 1 & 0 \end{pmatrix} 
\begin{pmatrix} 1 \\ 0 \end{pmatrix} = 1$$
行列であれば、
$$| 0 \rangle \langle 0 | = \begin{pmatrix} 1 \\ 0 \end{pmatrix} 
\begin{pmatrix} 1 & 0 \end{pmatrix} = \begin{pmatrix}
1 & 0 \\
0 & 0
\end{pmatrix}$$
のように二つをくっつけるだけで表せます。

本当はエルミート性も扱いたいですが、初学者でも直感的に学べることを念頭に置いているので、興味のある方はそちらの方も調べてもらうということにします。
とにもかくにも、この記法の意味と使い方を知っているだけで、応用になってもある程度ついていけるようになります。

## テンソル積
ここではテンソル積の計算の仕方と、どのような場面で使うのかということについて扱っていきます。
テンソル積は内積（ドット積）とも外積（クロス積）とも異なる、積の計算方法ですが、それほど難しいものではないです。ベクトル同士やベクトルと行列など様々な計算で使えます。

例としては、ベクトル同士だと
$$ \begin{pmatrix}
1 \\
0
\end{pmatrix} \otimes \begin{pmatrix}
0 \\
1
\end{pmatrix} = \begin{pmatrix}
1 \cdot 0 \\
1 \cdot 1 \\
0 \cdot 0 \\
0 \cdot 1
\end{pmatrix} = \begin{pmatrix}
0 \\
1 \\
0 \\
0
\end{pmatrix} $$

ベクトルと行列だと

$$
\begin{pmatrix} 1 \\ 0 \end{pmatrix} \otimes \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}
= \begin{pmatrix} 1 \cdot \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \\ 0 \cdot \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \end{pmatrix}
= \begin{pmatrix} 1 & 0 \\ 0 & 1 \\ 0 & 0 \\ 0 & 0 \end{pmatrix}
$$

行列同士だと

$$
\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \otimes \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} = 
\begin{pmatrix} 1 \cdot  \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} & 0 \cdot  \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \\ 0 \cdot  \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} & 1 \cdot  \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} \end{pmatrix}
= \begin{pmatrix}
  1 & 0 & 0 & 0 \\
  0 & 1 & 0 & 0 \\
  0 & 0 & 1 & 0 \\
  0 & 0 & 0 & 1
\end{pmatrix}
$$
というように計算します。右のベクトルや行列を左側の各要素に掛けていくイメージです。

今回扱ったディラック記法とテンソル積はこの先の説明で多く用いますので、もし今後計算についていけなくなったらこちらのページを定期的に見返すようにしてみてください。

次回は「ブロッホ球を用いた捉え方」です。
➡️ **[Step 03: ブロッホ球を用いた捉え方](./03_bloch_sphere.md)**