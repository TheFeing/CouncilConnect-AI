for f in *.tf; do 
    echo "-----------------------------------" >> ../../../../../ngfei/Downloads/temp.txt
    echo "FILE: $f" >> ../../../../../ngfei/Downloads/temp.txt
    echo "-----------------------------------" >> ../../../../../ngfei/Downloads/temp.txt
    cat "$f" >> ../../../../../ngfei/Downloads/temp.txt
    echo -e "\n" >> ../../../../../ngfei/Downloads/temp.txt
done