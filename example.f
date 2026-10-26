program Main
  integer x = 1;
  integer sum = 0;
  while (x <= 100)
    if (x > 10)
      sum = sum + x;
    else
      sum = sum - x;
    endif
    x = x + 1;
  endwhile
  print(sum);
endprogram
